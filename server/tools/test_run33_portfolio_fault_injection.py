#!/usr/bin/env python3
"""
RUN 33: THE REQUIRED 25-FAULT PORTFOLIO HEALTH CAMPAIGN.

WHAT A FAULT MUST DO TO COUNT. Baseline GREEN; the mutation APPLIED and CONFIRMED APPLIED by
reading the mutated state back rather than assuming it took; a NAMED GUARD going RED FOR THE
INTENDED REASON; restore; caches cleared where a source file was touched; baseline GREEN again.

FIVE WAYS A CAMPAIGN LIKE THIS HAS LIED IN THIS REPOSITORY, and each is refused here:
  1. a crash instead of a failure -- an exception raised BY THE MUTATION is not a RED, and every
     source mutation runs in a subprocess whose exception is reported as a CRASH and scored zero;
  2. an injection that silently failed to apply -- every fault reads its mutation back;
  3. a fixture that builds state by a route production does not take -- the route faults execute
     the real dispatcher and read the real call site;
  4. an assertion against a copy of the logic -- every expectation is the supplied contract's;
  5. an assertion of the defect's own sentence -- every guard asserts on VALUES and STRUCTURE.

SOURCE MUTATIONS DROP __pycache__ ON BOTH SIDES. A restore inside the same clock second changes
neither mtime nor size, so a cached mutant survives; the cache is removed before and after every
source edit and every source fault runs in a fresh interpreter with bytecode writing disabled.

Writes code_audit/run33_portfolio_fault_injection_results.csv.
"""

from __future__ import annotations

import csv
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / "tools"))

from app.simulation import canonical_v8 as V8                          # noqa: E402

from campaign_safety import arm, snapshot_text   # noqa: E402

OUT = ROOT / "code_audit" / "run33_portfolio_fault_injection_results.csv"
FIXTURES = ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.5" / "package_D_portfolio_health"
REQUIRED = 25

PASSED = 0
FAILED = 0
FAILURES: list[str] = []
ROWS: list[list[str]] = [["fault", "target", "mutation", "applied", "confirmed_applied",
                          "guard", "intended_red", "crash_accepted_as_red", "restored_green",
                          "result"]]
REDS = 0
APPLIED = 0
RESTORED = 0
CRASHES = 0


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


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def drop_pycache():
    for d in (ROOT / "server").rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


# =================================================================================================
# MECHANISM A: A SOURCE FAULT. Real production source is rewritten, a probe runs in a FRESH
# interpreter, and the source is restored. The probe body is supplied per fault so the guard can
# observe whatever the fault is about -- the same forest twice, the live call site, the registry.
# =================================================================================================

PROBE_HEAD = r'''
import json, sys, pathlib
sys.path.insert(0, sys.argv[1])
sys.path.insert(0, sys.argv[1] + "/tools")
def emit(d):
    print("VERDICT" + json.dumps(d, default=str))
try:
'''
PROBE_TAIL = r'''
except Exception as exc:                                              # noqa: BLE001
    emit({"ok": False, "crash": repr(exc)})
'''


def run_probe(body: str, arg: str = "") -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = pathlib.Path(tmp)
        src = PROBE_HEAD + "\n".join("    " + ln for ln in body.strip("\n").splitlines()) \
            + "\n" + PROBE_TAIL
        (tmp / "probe.py").write_text(src, encoding="utf-8")
        r = subprocess.run([sys.executable, str(tmp / "probe.py"), str(ROOT / "server"), arg],
                           capture_output=True, text=True,
                           env={"PYTHONIOENCODING": "utf-8", "PATH": "/usr/bin:/bin",
                                "PYTHONDONTWRITEBYTECODE": "1"})
    for line in r.stdout.splitlines():
        if line.startswith("VERDICT"):
            return json.loads(line[len("VERDICT"):])
    return {"ok": False, "crash": f"no verdict (rc={r.returncode}) {r.stderr[-400:]}"}


#: The standard probe: run the canonical layer over one governed fixture and return its results.
STANDARD_PROBE = '''
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
run = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], fx["feature_records"],
                                  fx.get("histories", []))
emit({"ok": True, "results": run["results"]})
'''


def source_fault(n, target, path, old, new, mutation, guard_name, guard,
                 body=STANDARD_PROBE, arg=None, fixture_name="ph1_isolation_forest_fixture.json",
                 also=()):
    """
    `also` carries further (old, new) pairs applied to the SAME file in the same mutation, for a
    defect that cannot be expressed at one anchor -- an order dependence, for instance, needs
    both the ordering and the tie-break to move, and mutating one of them alone would leave the
    property standing and the campaign would credit a fault it had not proved.
    """
    global REDS, APPLIED, RESTORED, CRASHES
    arg = arg if arg is not None else str(FIXTURES / fixture_name)
    f = ROOT / path
    # Snapshot from the COMMITTED bytes at HEAD, never from disk.
    original = snapshot_text(ROOT, path)
    drop_pycache()
    base = run_probe(body, arg)
    green_before = check(base.get("ok") is True and guard(base) is True,
                         f"F{n} GREEN BEFORE: {guard_name}",
                         str(base.get("crash", ""))[:120])
    applied = confirmed = red = crash = False
    edits = [(old, new)] + list(also)
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
                red = check(guard(got) is False,
                            f"F{n} RED for the intended reason: {guard_name}")
    finally:
        f.write_text(original, encoding="utf-8")
        drop_pycache()
    after = run_probe(body, arg)
    restored = check(f.read_text(encoding="utf-8") == original and after.get("ok") is True
                     and guard(after) is True,
                     f"F{n} RESTORED GREEN: source byte-identical, guard green again")
    APPLIED += 1 if applied else 0
    REDS += 1 if red else 0
    RESTORED += 1 if restored else 0
    CRASHES += 1 if crash else 0
    ROWS.append([str(n), target, mutation, "YES" if applied else "NO",
                 "YES" if confirmed else "NO", guard_name, "YES" if red else "NO",
                 "YES" if crash else "NO", "YES" if restored else "NO",
                 "PASS" if (green_before and applied and confirmed and red and restored
                            and not crash) else "FAIL"])


# =================================================================================================
# MECHANISM B: A DATA FAULT. The GOVERNED STRUCTURE the module is given is mutated -- which is
# what the defect being tested actually is for a contract violation -- the mutation is read back,
# and the module's own guard must refuse it.
# =================================================================================================

def data_fault(n, target, mutation, guard_name, baseline, mutate, guard):
    global REDS, APPLIED, RESTORED, CRASHES
    base = baseline()
    green_before = check(guard(base) is True, f"F{n} GREEN BEFORE: {guard_name}")
    applied = confirmed = red = crash = False
    try:
        mutated, evidence = mutate()
        applied = True
        confirmed = check(bool(evidence),
                          f"F{n} INJECTION CONFIRMED: {evidence}", str(evidence)[:130])
        red = check(guard(mutated) is False, f"F{n} RED for the intended reason: {guard_name}")
    except Exception as exc:                                          # noqa: BLE001
        crash = True
        check(False, f"F{n} CRASHED rather than failing a guard -- NOT counted as RED",
              repr(exc)[:200])
    restored = check(guard(baseline()) is True, f"F{n} RESTORED GREEN: {guard_name}")
    APPLIED += 1 if applied else 0
    REDS += 1 if red else 0
    RESTORED += 1 if restored else 0
    CRASHES += 1 if crash else 0
    ROWS.append([str(n), target, mutation, "YES" if applied else "NO",
                 "YES" if confirmed else "NO", guard_name, "YES" if red else "NO",
                 "YES" if crash else "NO", "YES" if restored else "NO",
                 "PASS" if (green_before and applied and confirmed and red and restored
                            and not crash) else "FAIL"])


import math                                                            # noqa: E402


def _c_expected(n: int) -> float:
    """c(n) from the PUBLISHED closed form, recomputed here rather than read from the module."""
    if n <= 1:
        return 0.0
    if n == 2:
        return 1.0
    return 2.0 * (math.log(n - 1) + 0.5772156649015329) - 2.0 * (n - 1) / n


def _probe_slope(v):
    from fractions import Fraction as _F
    return _F(v["slope"]) if v.get("slope") else None


def _no_reinforcement(d):
    """No project profile gained an evidence body or a confidence when a lineage was duplicated."""
    return all(b["confidence"] is None and b["corroboration_established"] is False
               and b["score"] is None for b in d["projects"].values())


PH1 = fixture("ph1_isolation_forest_fixture.json")
PH2 = fixture("ph2_midrank_percentile_fixture.json")
PH3 = fixture("ph3_trajectory_slope_fixture.json")
PH4 = fixture("ph4_nearest_neighbour_fixture.json")
PH5 = fixture("ph5_component_profile_fixture.json")


def run_fx(fx, records=None, schema=None, cohort=None, histories=None):
    return V8.compute_portfolio_health(cohort or fx["cohort"], schema or fx["feature_schema"],
                                       records if records is not None else fx["feature_records"],
                                       histories if histories is not None
                                       else fx.get("histories", []))


def res(fx, key, **kw):
    return run_fx(fx, **kw)["results"][key]


IF_KEY = "cat8_1_isolation_forest"
OUT_KEY = "cat8_2_portfolio_outlier"
TRJ_KEY = "cat8_3_trajectory_classifier"
PAT_KEY = "cat8_4_cross_project_pattern"
ANM_KEY = "cat8_5_anomaly_score"


# =================================================================================================
# THE START GUARD. See server/tools/campaign_safety.py for why an end-only check is useless.
arm(ROOT, "run33 portfolio fault injection", allow=[OUT])

head("FAULTS 1-8: PH.1 ISOLATION FOREST")
# =================================================================================================

# --- 1. the production route uses the retired distance proxy ------------------------------------
ROUTE_PROBE = '''
from app.simulation import portfolio_health as PH
bad = []
PH.assert_not_reachable(lambda cond, name, detail="": bad.append(name) if not cond else None)
emit({"ok": True, "failures": bad})
'''
source_fault(
    1, "PH.1 production route (documents.run_and_store)", "server/app/documents.py",
    "    snapshot = compute_portfolio_health_snapshot(",
    "    from .simulation.portfolio import compute_portfolio\n"
    "    snapshot = compute_portfolio(",
    "production's only portfolio call site is repointed at the retired v20 distance-proxy "
    "implementation",
    "portfolio_health.assert_not_reachable, read from the LIVE call-site source",
    lambda v: v.get("failures") == [],
    body=ROUTE_PROBE)

# --- 2. omits random isolation trees ------------------------------------------------------------
source_fault(
    2, "PH.1 canonical_v8.isolation_forest", "server/app/simulation/canonical_v8.py",
    "    forest = IsolationForest(vectors, n_trees=n_trees,",
    "    n_trees = 1\n    forest = IsolationForest(vectors, n_trees=n_trees,",
    "the ENSEMBLE is removed: a single tree replaces the hundred the published default grows, so "
    "E[h(x)] is one draw rather than an expectation",
    "PH.1 reports the published ensemble size, and E[h(x)] is an expectation over it",
    lambda v: v["results"][IF_KEY]["model"]["n_trees"] == 100)

# --- 3. wrong c(n) ------------------------------------------------------------------------------
source_fault(
    3, "PH.1 isolation_forest.c_factor", "server/app/simulation/isolation_forest.py",
    "    return 2.0 * harmonic(n - 1) - 2.0 * (n - 1) / n",
    "    return 2.0 * harmonic(n - 1)",
    "c(n) drops the -2(n-1)/n term of the published closed form",
    "the reported normaliser is c(psi) = 2H(psi-1) - 2(psi-1)/psi, recomputed here from the "
    "published closed form and not read back from the module",
    lambda v: abs(v["results"][IF_KEY]["model"]["normaliser_c_psi"]
                  - _c_expected(v["results"][IF_KEY]["model"]["subsample_psi"])) < 1e-9)

# --- 4. omits the external-node path correction -------------------------------------------------
source_fault(
    4, "PH.1 isolation_forest._path_length", "server/app/simulation/isolation_forest.py",
    "        return depth + c_factor(node.size)",
    "        return depth",
    "the external-node adjustment c(size) is dropped, so a node holding several points is "
    "treated as if it had isolated one",
    "at least one project's mean path length exceeds the tree height limit, which is only "
    "possible when the external-node adjustment is being added",
    lambda v: max(p["mean_path_length"] for p in v["results"][IF_KEY]["projects"].values())
    > v["results"][IF_KEY]["model"]["height_limit"])

# --- 5. separate incomparable forests (LOAD-BEARING) --------------------------------------------
ONE_FOREST_PROBE = '''
from app.simulation import canonical_v8 as V8
from app.simulation.isolation_forest import IsolationForest
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
cohort = V8.PortfolioCohort(fx["cohort"], fx["feature_schema"], fx["feature_records"])
d = V8.isolation_forest(cohort)
feats = [f for f in cohort.features if f.required]
X = [[cohort.value(m, f) for f in feats] for m in cohort.members]
# INDEPENDENTLY refit ONE forest here, on the whole cohort, with the model metadata the module
# reported, and score every member from it. If the module really used one forest, its scores are
# these scores. If it fitted a forest per project, they are not.
one = IsolationForest(X, n_trees=d["model"]["n_trees"],
                      subsample=d["model"]["subsample_psi"], seed=d["model"]["seed"])
mine = {p: one.anomaly_score(x) for p, x in zip(cohort.project_ids, X)}
theirs = {p: v["anomaly_score"] for p, v in d["projects"].items()}
emit({"ok": True, "same": all(abs(mine[p] - theirs[p]) < 1e-12 for p in mine),
      "population": sorted(d["model"]["fitted_project_population"]),
      "members": sorted(theirs)})
'''
source_fault(
    5, "PH.1 canonical_v8.isolation_forest", "server/app/simulation/canonical_v8.py",
    "    for m, v in zip(cohort.members, vectors):\n        score = forest.anomaly_score(v)",
    "    for m, v in zip(cohort.members, vectors):\n"
    "        _ref = [w for w in vectors if w is not v]\n"
    "        score = IsolationForest(_ref, n_trees=n_trees,\n"
    "                                subsample=min(subsample, len(_ref)),\n"
    "                                seed=seed).anomaly_score(v)",
    "every project is scored by its OWN forest fitted on the other projects -- the v20 behaviour "
    "section 6 forbids -- so the scores displayed together are on different scales",
    "every score reported together IS the score ONE forest fitted on the whole cohort produces, "
    "recomputed independently in the probe from the reported model metadata",
    lambda v: v.get("same") is True and v.get("population") == v.get("members"),
    body=ONE_FOREST_PROBE)

# --- 6. non-reproducible seed -------------------------------------------------------------------
SEED_PROBE = '''
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
a = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], fx["feature_records"], [])
b = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], fx["feature_records"], [])
ka = {p: v["anomaly_score"] for p, v in a["results"]["cat8_1_isolation_forest"]["projects"].items()}
kb = {p: v["anomaly_score"] for p, v in b["results"]["cat8_1_isolation_forest"]["projects"].items()}
emit({"ok": True, "reproducible": ka == kb,
      "seed": a["results"]["cat8_1_isolation_forest"]["model"]["seed"]})
'''
source_fault(
    6, "PH.1 isolation_forest.IsolationForest", "server/app/simulation/isolation_forest.py",
    "        rng = random.Random(seed)",
    "        rng = random.Random()",
    "the ensemble stops being seeded: the declared seed is recorded on the model but the trees "
    "are drawn from an unseeded generator, so the same cohort returns different scores",
    "two independent computations of the same cohort return IDENTICAL scores",
    lambda v: v.get("reproducible") is True,
    body=SEED_PROBE)

# --- 7. a degenerate cohort emits an authoritative anomaly flag ---------------------------------
def _f7():
    c = dict(PH1["cohort"], project_ids=["IN-01"])
    d = res(PH1, IF_KEY, cohort=c, records=[PH1["feature_records"][0]])
    return d, (f"cohort reduced to {len(c['project_ids'])} declared project; eligible members "
               f"{d['cohort']['cohort_size'] if d.get('cohort') else 0}")


data_fault(
    7, "PH.1 degenerate cohort", "the governed cohort is reduced to a single project",
    "a cohort with fewer than two eligible members abstains under an explicit "
    "INSUFFICIENT_COHORT disposition and emits no anomaly score or flag for any project",
    lambda: res(PH1, IF_KEY), _f7,
    lambda d: (not d.get("abstained")) and bool(d.get("projects")))

# --- 8. unit rescaling changes the substantive rank ---------------------------------------------
# THE PUBLISHED CONSTRUCTION IS EQUIVARIANT UNDER AN AFFINE RESCALING of a feature, because the
# split is drawn uniformly between that attribute's OBSERVED MINIMUM AND MAXIMUM: the same seed
# maps every split through the same affine map, and the ordering is preserved exactly. The
# mutation contaminates the score with the RAW FEATURE MAGNITUDE, which is scale-dependent by
# construction, and the substantive ordering then moves under the declared rescaling.
SCALE_PROBE = """
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())


def top(recs):
    d = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], recs,
                                    [])["results"]["cat8_1_isolation_forest"]
    return sorted(d["projects"], key=lambda p: -d["projects"][p]["anomaly_score"])[0]


plain = top(fx["feature_records"])
scaled = top([dict(r, values={k: v * 1000.0 + 7.0 for k, v in r["values"].items()})
              for r in fx["feature_records"]])
emit({"ok": True, "same_top": plain == scaled, "plain": plain, "scaled": scaled})
"""
source_fault(
    8, "PH.1 canonical_v8.isolation_forest", "server/app/simulation/canonical_v8.py",
    "        score = forest.anomaly_score(v)",
    "        score = forest.anomaly_score(v) + 1e-3 * sum(v)",
    "the anomaly score is contaminated by the RAW FEATURE MAGNITUDE, so the reading depends on "
    "the units the features happen to be recorded in",
    "the most anomalous project is UNCHANGED under the declared affine rescaling x -> 1000x + 7",
    lambda v: v.get("same_top") is True,
    body=SCALE_PROBE)


# =================================================================================================
head("FAULTS 9-11: PH.2 PORTFOLIO OUTLIER DETECTION")
# =================================================================================================

# --- 9. PH.2 calls itself a learned ML model ----------------------------------------------------
source_fault(
    9, "PH.2 canonical_v8.portfolio_outlier", "server/app/simulation/canonical_v8.py",
    '        "is_learned_model": False,',
    '        "is_learned_model": True,',
    "PH.2 declares itself a learned machine-learning model, which it is not: nothing is trained "
    "and no parameter is estimated from data",
    "PH.2 declares is_learned_model false and is_probability_of_failure false, and its method "
    "note says nothing is trained or fitted",
    lambda v: v["results"][OUT_KEY]["is_learned_model"] is False
    and v["results"][OUT_KEY]["is_probability_of_failure"] is False
    and "not a learned machine learning model" in v["results"][OUT_KEY]["method_note"],
    fixture_name="ph2_midrank_percentile_fixture.json")

# --- 10. tie handling changes with project order -------------------------------------------------
# THE MIDRANK IS WHAT MAKES TIES ORDER-INDEPENDENT: a tied value contributes 0.5 to its own rank
# and the answer does not depend on where in the list it sat. The mutation replaces it with a
# POSITIONAL rank -- the index of the value in the pool -- which is exactly the family of defect
# a "less than or equal" count belongs to, and ties then depend on arrival order.
TIE_PROBE = """
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())


def ranks(recs):
    # RUN 34: the composite is withheld absent governed weights, so the midranks this fault is
    # about are read from the per-feature profile, which is where they now live.
    d = V8.compute_portfolio_health(fx["tie_cohort"], fx["feature_schema"], recs,
                                    [])["results"]["cat8_2_portfolio_outlier"]
    return {p: v["feature_percentiles_exact"] for p, v in d["projects"].items()}


fwd = ranks(fx["tie_feature_records"])
rev = ranks(list(reversed(fx["tie_feature_records"])))
emit({"ok": True, "order_independent": fwd == rev,
      "ties_equal": fwd.get("T-A") == fwd.get("T-B"), "fwd": fwd, "rev": rev})
"""
source_fault(
    10, "PH.2 canonical_v8._midrank", "server/app/simulation/canonical_v8.py",
    "    less = sum(1 for v in values if v < x)\n"
    "    equal = sum(1 for v in values if v == x)\n"
    "    return (Fraction(less) + Fraction(equal, 2)) / Fraction(len(values))",
    "    return Fraction(sorted(values).index(x) + values.index(x) % 2) / Fraction(len(values))",
    "the midrank is replaced by a POSITIONAL rank, so a tied project's percentile depends on "
    "where in the cohort its record happened to arrive",
    "the two tied projects receive the SAME midrank, and every project's midrank is identical "
    "whichever order the records arrive in",
    lambda v: v.get("order_independent") is True and v.get("ties_equal") is True,
    also=[('        self.members.sort(key=lambda m: m["project_id"])',
           "        pass  # members left in arrival order")],
    body=TIE_PROBE, fixture_name="ph2_midrank_percentile_fixture.json")

# --- 11. silently drops a missing feature and reweights ------------------------------------------
_TWO_FEATURE_SCHEMA = {"version": "sv2f", "features": [
    dict(PH2["feature_schema"]["features"][0], feature_id="f_a", label="f_a"),
    dict(PH2["feature_schema"]["features"][0], feature_id="f_b", label="f_b")]}
_TF_COHORT = dict(PH2["cohort"], cohort_id="C2F", feature_schema_version="sv2f")
_TF_RECORDS = [dict(r, cohort_id="C2F", feature_schema_version="sv2f",
                    values={"f_a": r["values"]["f_adverse"], "f_b": r["values"]["f_adverse"]})
               for r in PH2["feature_records"]]


def _f11():
    hurt = [dict(_TF_RECORDS[0], values={"f_a": _TF_RECORDS[0]["values"]["f_a"]},
                 missing_fields=["f_b"])] + _TF_RECORDS[1:]
    d = V8.compute_portfolio_health(_TF_COHORT, _TWO_FEATURE_SCHEMA, hurt, [])["results"][OUT_KEY]
    return d, (f"{hurt[0]['project_id']} now declares f_b missing; read back: "
               f"missing_fields={hurt[0]['missing_fields']}")


data_fault(
    11, "PH.2 missing required feature", "a required governed feature is removed from one project",
    "PH.2 ABSTAINS on a missing required feature: the feature is not silently dropped and the "
    "remaining features are not renormalised over a smaller set",
    lambda: V8.compute_portfolio_health(_TF_COHORT, _TWO_FEATURE_SCHEMA, _TF_RECORDS,
                                        [])["results"][OUT_KEY],
    _f11,
    lambda d: (not d.get("abstained"))
    and len(d["projects"]["P-A"]["feature_percentiles"]) == 2)


# =================================================================================================
head("FAULTS 12-14: PH.3 SIGNAL TRAJECTORY CLASSIFIER")
# =================================================================================================

_H3 = [h for h in PH3["histories"] if h["project_id"] == "P-EVEN"]
_C3 = dict(PH3.get("cohort") or PH2["cohort"], cohort_id="C3",
           project_ids=["P-EVEN", "P-IRREGULAR", "P-CONSTANT"])
_R3 = [dict(r, project_id=p, cohort_id="C3")
       for p, r in zip(_C3["project_ids"], PH2["feature_records"])]


def _traj(histories):
    return V8.compute_portfolio_health(_C3, PH2["feature_schema"], _R3, histories)["results"][
        TRJ_KEY]


from fractions import Fraction                                          # noqa: E402


def _slope_is_exact(d):
    if d.get("abstained"):
        return False
    body = (d["projects"].get("P-EVEN") or [None])[0]
    return body is not None and Fraction(body["ols_slope_exact"]) == Fraction(-1, 10)


# --- 12. divides the endpoint change by the number of observations ------------------------------
source_fault(
    12, "PH.3 canonical_v8.ols_slope", "server/app/simulation/canonical_v8.py",
    "    num = sum(((t - tbar) * (x - xbar) for t, x in zip(times, values)), Fraction(0))\n"
    "    den = sum(((t - tbar) ** 2 for t in times), Fraction(0))",
    "    num = values[-1] - values[0]\n    den = Fraction(len(times))",
    "the OLS fit is replaced by the endpoint change divided by the NUMBER OF OBSERVATIONS -- "
    "three observations contain two intervals, and this divides the same rise by three",
    "the slope on t=[0,1,2], x=[1.0,0.9,0.8] is exactly -1/10, computed here from the supplied "
    "oracle and not read back from the module",
    lambda v: _probe_slope(v) == Fraction(-1, 10),
    body='''
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
c = {"cohort_id": "C3", "portfolio_id": "PF", "project_ids": ["P-EVEN"], "period": "2026-01",
     "inclusion_rule": "all", "exclusion_rule": "none", "feature_schema_version": "s",
     "qualification_policy": "q", "model_version": "m"}
sch = {"version": "s", "features": [{"feature_id": "f", "label": "f", "units": "u",
       "orientation": "HIGHER_IS_MORE_ADVERSE", "scaling_rule": "n", "missingness_rule": "a",
       "source_module": "t", "qualification_requirement": "c"}]}
rec = [{"project_id": "P-EVEN", "cohort_id": "C3", "period": "2026-01", "values": {"f": 1.0},
        "qualification_state": "QUALIFIED", "missing_fields": [], "invalid_fields": [],
        "source_lineage": "L", "source_provenance": "P", "feature_schema_version": "s"}]
h = [x for x in fx["histories"] if x["project_id"] == "P-EVEN"]
d = V8.compute_portfolio_health(c, sch, rec, h)["results"]["cat8_3_trajectory_classifier"]
b = (d.get("projects", {}).get("P-EVEN") or [None])[0]
emit({"ok": True, "slope": b["ols_slope_exact"] if b else None,
      "abstained": d.get("abstained")})
''',
    fixture_name="ph3_trajectory_slope_fixture.json")

# --- 13. ignores the actual time intervals ------------------------------------------------------
def _f13():
    # The irregular series is re-supplied with LIST POSITION as time: the defect exactly.
    flat = [dict(h, observations=[dict(o, reporting_time=i)
                                  for i, o in enumerate(h["observations"])])
            for h in PH3["histories"] if h["project_id"] == "P-IRREGULAR"]
    d = _traj(flat)
    body = (d["projects"].get("P-IRREGULAR") or [None])[0]
    return (body, f"reporting times replaced by list position 0,1,2; read back: "
            f"{[o['reporting_time'] for o in flat[0]['observations']]}")


_IRR = (_traj([h for h in PH3["histories"] if h["project_id"] == "P-IRREGULAR"])
        ["projects"]["P-IRREGULAR"][0])
data_fault(
    13, "PH.3 reporting time", "the actual reporting dates are replaced by list position",
    "the fitted slope is the slope over the ACTUAL reporting interval: 2026-01-01, 01-08 and "
    "03-01 are 0, 7 and 59 days apart, and the slope per day differs from the slope over "
    "positions 0, 1, 2",
    lambda: _IRR, _f13,
    lambda b: b is not None and Fraction(b["ols_slope_exact"]) == Fraction(
        _IRR["ols_slope_exact"]))

# --- 14. mixes different signal identities ------------------------------------------------------
def _f14():
    mixed = [dict(_H3[0], observations=[
        dict(_H3[0]["observations"][0]),
        dict(_H3[0]["observations"][1], signal_id="a_different_signal"),
        dict(_H3[0]["observations"][2])])]
    d = _traj(mixed)
    return d, ("the middle observation now carries signal identity 'a_different_signal'; read "
               f"back: {[o.get('signal_id', 'cost_index') for o in mixed[0]['observations']]}")


data_fault(
    14, "PH.3 signal identity", "one observation is given a different stable signal identity",
    "two different signals are never fitted as one trajectory: the history is refused rather "
    "than blended",
    lambda: _traj(_H3), _f14, _slope_is_exact)


# =================================================================================================
head("FAULTS 15-18: PH.4 CROSS-PROJECT PATTERN DETECTOR")
# =================================================================================================

def _pat(**kw):
    return res(PH4, PAT_KEY, **kw)


_PAT_BASE = _pat()

# --- 15. includes the self-match ----------------------------------------------------------------
source_fault(
    15, "PH.4 canonical_v8.cross_project_pattern", "server/app/simulation/canonical_v8.py",
    "        peers = sorted(q for q in ids if q != pid)      # SELF-MATCH EXCLUDED",
    "        peers = sorted(ids)",
    "the project itself is left in its own peer set, so every project's nearest neighbour is "
    "itself at distance 0 and similarity 1",
    "no project appears in its own neighbour set or its own distance table",
    lambda v: all(p not in b["nearest_neighbour_project_ids"] and p not in b["all_distances"]
                  for p, b in v["results"][PAT_KEY]["projects"].items()),
    fixture_name="ph4_nearest_neighbour_fixture.json")

# --- 16. retains the unvalidated fixed match radius ---------------------------------------------
source_fault(
    16, "PH.4 canonical_v8.cross_project_pattern", "server/app/simulation/canonical_v8.py",
    '        "match_threshold": None,',
    '        "match_threshold": 0.15,',
    "the unvalidated 0.15 match radius from v20 is reinstated as an operational threshold",
    "PH.4 applies NO match threshold and reports the continuous relationship instead",
    lambda v: v["results"][PAT_KEY]["match_threshold"] is None,
    fixture_name="ph4_nearest_neighbour_fixture.json")

# --- 17. a healthy nearest peer automatically creates adverse status ----------------------------
source_fault(
    17, "PH.4 canonical_v8.cross_project_pattern", "server/app/simulation/canonical_v8.py",
    '        "similarity_is_not_failure": True,',
    '        "similarity_is_not_failure": False,\n'
    '        "status_color": "Amber",',
    "matching a peer is turned into an adverse status: a status colour is emitted from the "
    "existence of a nearest neighbour",
    "PH.4 emits no status colour and declares that similarity is not failure",
    lambda v: "status_color" not in v["results"][PAT_KEY]
    and v["results"][PAT_KEY]["similarity_is_not_failure"] is True,
    fixture_name="ph4_nearest_neighbour_fixture.json")


# --- 18. the result changes with project order --------------------------------------------------
# TWO ANCHORS, because the property rests on two things: the cohort's members are held in a
# stable project-id order, and the nearest-neighbour tie-break returns ALL tied neighbours in
# ascending project-id order. Mutating either alone leaves the property standing, and a campaign
# that credited that would be crediting a fault it had not proved.
ORDER_PROBE = """
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())


def key(recs):
    d = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], recs,
                                    [])["results"]["cat8_4_cross_project_pattern"]
    return {p: [b["nearest_neighbour_project_ids"], round(b["distance"], 12)]
            for p, b in d["projects"].items()}


fwd = key(fx["feature_records"])
rev = key(list(reversed(fx["feature_records"])))
emit({"ok": True, "order_independent": fwd == rev, "fwd": fwd, "rev": rev})
"""
source_fault(
    18, "PH.4 canonical_v8.cross_project_pattern", "server/app/simulation/canonical_v8.py",
    "        nearest = sorted(q for q in peers if dists[q] == best)",
    "        nearest = [q for q in peers if dists[q] == best][:1]",
    "the declared tie rule is dropped: instead of all tied neighbours in ascending project-id "
    "order, the FIRST tied neighbour in arrival order is returned",
    "every pairwise distance and every nearest-neighbour set is identical whichever order the "
    "records arrive in",
    lambda v: v.get("order_independent") is True,
    also=[('        self.members.sort(key=lambda m: m["project_id"])',
           "        pass  # members left in arrival order"),
          ("        peers = sorted(q for q in ids if q != pid)      # SELF-MATCH EXCLUDED",
           "        peers = [q for q in ids if q != pid]")],
    body=ORDER_PROBE, fixture_name="ph4_nearest_neighbour_fixture.json")


# =================================================================================================
head("FAULTS 19-22: PH.5 ANOMALY SCORE")
# =================================================================================================

def _anm(**kw):
    return res(PH5, ANM_KEY, **kw)


# --- 19. a constant placeholder -----------------------------------------------------------------
source_fault(
    19, "PH.5 canonical_v8.anomaly_profile", "server/app/simulation/canonical_v8.py",
    '            "confidence": None,\n            "score": None,',
    '            "confidence": 0.5,\n            "score": 0.5,',
    "a constant 0.5 placeholder is reinstated as the composite score and the confidence -- the "
    "v20 defect that pulled every project's composite toward the middle",
    "every project profile carries score None and confidence None, and the only number on a "
    "profile is its evidence-body count",
    lambda v: all(b["score"] is None and b["confidence"] is None
                  and [k for k, x in b.items()
                       if isinstance(x, (int, float)) and not isinstance(x, bool)]
                  == ["distinct_evidence_bodies"]
                  for b in v["results"][ANM_KEY]["projects"].values()),
    fixture_name="ph5_component_profile_fixture.json")


# --- 20. missing history changes the other effective weights -------------------------------------
# THE DEFECT IS INJECTED INTO PRODUCTION, not into the data: withdrawing the history is not a
# fault, it is an ordinary input. The fault is a line that makes PH.1's own model depend on
# whether a PH.3 history happens to exist -- which is exactly what "the effective weights changed
# when a constituent disappeared" looked like at v20.
MISSING_PROBE = """
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
with_h = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], fx["feature_records"],
                                     fx.get("histories", []))["results"]
without = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], fx["feature_records"],
                                      [])["results"]
same = all(json.dumps(with_h[k], sort_keys=True, default=str)
           == json.dumps(without[k], sort_keys=True, default=str)
           for k in ("cat8_1_isolation_forest", "cat8_2_portfolio_outlier",
                     "cat8_4_cross_project_pattern"))
prof = without["cat8_5_anomaly_score"]["projects"]
emit({"ok": True, "others_unmoved": same,
      "missing_named": all("D1.3" in b["missing_constituents"] for b in prof.values()),
      "no_weights": all(b["effective_weights"] is None for b in prof.values())})
"""
source_fault(
    20, "PH.5 canonical_v8.compute_portfolio_health", "server/app/simulation/canonical_v8.py",
    '        "cat8_1_isolation_forest": isolation_forest(cohort),',
    '        "cat8_1_isolation_forest": isolation_forest(\n'
    '            cohort, n_trees=(IF_TREES if histories else IF_TREES // 2)),',
    "PH.1's own ensemble size is made to depend on whether a PH.3 history exists, so a missing "
    "constituent silently changes the value of a constituent that is present",
    "a missing PH.3 constituent leaves PH.1, PH.2 and PH.4 BYTE-IDENTICAL, names D1.3 as a "
    "missing constituent, and renormalises nothing because there are no weights to renormalise",
    lambda v: v.get("others_unmoved") is True and v.get("missing_named") is True
    and v.get("no_weights") is True,
    body=MISSING_PROBE, fixture_name="ph5_component_profile_fixture.json")

# --- 21. duplicate lineage increases confidence (LOAD-BEARING) ----------------------------------
# THE DEFECT IS INJECTED INTO PRODUCTION. `distinct_evidence_bodies` counts EVIDENCE BODIES --
# the (cohort, schema, period) a constituent rests on -- so two transforms of one feature record
# count once. The mutation makes it count CONSTITUENTS instead and derives a confidence from
# that count, which is precisely "duplicate lineage raises confidence".
DUP_PROBE = """
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
run = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], fx["feature_records"],
                                  fx.get("histories", []))["results"]
cohort = V8.PortfolioCohort(fx["cohort"], fx["feature_schema"], fx["feature_records"])
honest = V8.anomaly_profile(cohort, {"D1.1": run["cat8_1_isolation_forest"],
                                     "D1.2": run["cat8_2_portfolio_outlier"],
                                     "D1.3": run["cat8_3_trajectory_classifier"],
                                     "D1.4": run["cat8_4_cross_project_pattern"]})
# THE SAME PH.1 RESULT OFFERED A SECOND TIME UNDER THE PH.2 SLOT.
dup = V8.anomaly_profile(cohort, {"D1.1": run["cat8_1_isolation_forest"],
                                  "D1.2": run["cat8_1_isolation_forest"],
                                  "D1.3": run["cat8_3_trajectory_classifier"],
                                  "D1.4": run["cat8_4_cross_project_pattern"]})
emit({"ok": True,
      "bodies_unchanged": all(dup["projects"][p]["distinct_evidence_bodies"]
                              == honest["projects"][p]["distinct_evidence_bodies"]
                              for p in honest["projects"]),
      "no_confidence": all(b["confidence"] is None for b in dup["projects"].values()),
      "no_corroboration": all(b["corroboration_established"] is False
                              for b in dup["projects"].values())})
"""
source_fault(
    21, "PH.5 canonical_v8.anomaly_profile", "server/app/simulation/canonical_v8.py",
    '        bodies = sorted({(c["cohort_id"], c["feature_schema_version"], c["period"])\n'
    '                         for c in present.values()})',
    '        bodies = sorted(present)',
    "the evidence-body count is replaced by a count of CONSTITUENTS, so the same result offered "
    "twice under two module ids reads as two supporting observations",
    "duplicate lineage does not raise confidence: the distinct-evidence-body count is unchanged, "
    "confidence stays null and corroboration stays false",
    lambda v: v.get("bodies_unchanged") is True and v.get("no_confidence") is True
    and v.get("no_corroboration") is True,
    also=[('            "confidence": None,',
           '            "confidence": min(1.0, 0.25 * len(present)),')],
    body=DUP_PROBE, fixture_name="ph5_component_profile_fixture.json")

# --- 22. a scalar without governed transformations/weights --------------------------------------
source_fault(
    22, "PH.5 canonical_v8.anomaly_profile", "server/app/simulation/canonical_v8.py",
    '        "score": None,\n        "score_blocked_reason": _blocked_reason,',
    '        "score": 0.42,\n        "score_blocked_reason": _blocked_reason,',
    "a scalar composite and a weight set are emitted although no governed normalisation, "
    "transformation, weight set, missingness policy or calibration objective exists",
    "PH.5 emits no scalar and no weights, and its disposition is PARAMETER_PROVENANCE_BLOCKED",
    lambda v: v["results"][ANM_KEY]["score"] is None
    and v["results"][ANM_KEY]["weights"] is None
    and v["results"][ANM_KEY]["disposition"] == "PARAMETER_PROVENANCE_BLOCKED",
    also=[('        "weights": None,\n        "projects": profiles,',
           '        "weights": {"D1.1": 0.5, "D1.2": 0.5},\n        "projects": profiles,')],
    fixture_name="ph5_component_profile_fixture.json")


# =================================================================================================
head("FAULTS 23-25: THE GOVERNANCE BOUNDARY")
# =================================================================================================

# --- 23. portfolio output enters Project Status or voting (LOAD-BEARING) ------------------------
VOTE_PROBE = '''
import inspect
from app import documents as D
from app.simulation.registry import CORE_VOTING_MODULES
src = inspect.getsource(D.run_and_store)
head = src.split("module_results=")[1].split(",")[0] if "module_results=" in src else ""
emit({"ok": True,
      "voting_count": len(CORE_VOTING_MODULES),
      "ph_in_vote": sorted(set(CORE_VOTING_MODULES) & {"D1.1","D1.2","D1.3","D1.4","D1.5"}),
      "modules_from_run": head.strip(),
      "snapshot_own_column": "portfolio_snapshot=snapshot" in src})
'''
source_fault(
    23, "the governance boundary (documents.run_and_store)", "server/app/documents.py",
    "        module_results=run.get(\"modules\"),",
    "        module_results=(run.get(\"modules\") or []) + list(\n"
    "            (snapshot.get(\"results\") or {}).values()),",
    "the portfolio readings are merged into `module_results`, the field Project Status, the "
    "category rollups, fusion and the vote all read",
    "the portfolio snapshot is stored ONLY on its own column, `module_results` comes from the "
    "project run alone, and no D1 identity is in the two-module voting set",
    lambda v: v.get("modules_from_run") == 'run.get("modules")'
    and v.get("snapshot_own_column") is True
    and v.get("ph_in_vote") == [] and v.get("voting_count") == 2,
    body=VOTE_PROBE)


# --- 24. mixed cohort periods and schemas are accepted -------------------------------------------
# ONE fault, BOTH checks: the comparability guard is a single boundary and disabling half of it
# would leave the other half green and the campaign would credit a fault it had not proved.
source_fault(
    24, "the cohort comparability guard", "server/app/simulation/canonical_v8.py",
    "            if str(raw[\"period\"]) != self.period:",
    "            if False:",
    "the mixed-reporting-period check is disabled, so records from two different periods enter "
    "one comparison as though the portfolio had been observed at one moment",
    "a cohort whose members do not share ONE period and ONE feature schema is refused: both "
    "halves of the comparability boundary are exercised in the same probe",
    lambda v: v.get("period_rejected") is True and v.get("schema_rejected") is True,
    body="""
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())


def _reject(recs, needle):
    run = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], recs, [])
    r = run["results"]["cat8_4_cross_project_pattern"]
    return bool(r.get("abstained")) and needle in (r.get("abstention_reason") or "")


mixed_period = [dict(fx["feature_records"][0], period="2026-09")] + fx["feature_records"][1:]
mixed_schema = ([dict(fx["feature_records"][0], feature_schema_version="OTHER")]
                + fx["feature_records"][1:])
emit({"ok": True,
      "period_rejected": _reject(mixed_period, "Mixed reporting periods are rejected"),
      "schema_rejected": _reject(mixed_schema, "Mixed feature schemas")})
""",
    fixture_name="ph4_nearest_neighbour_fixture.json")


# --- 25. a missing Category-9 assessment bypasses Portfolio Health -------------------------------
source_fault(
    25, "the Category-9 qualification boundary", "server/app/simulation/canonical_v8.py",
    "            if state not in ELIGIBLE_STATES:",
    "            if False:",
    "the Category-9 eligibility gate is removed, so UNASSESSED evidence enters the cohort and "
    "is analysed as though it had been assessed",
    "an UNASSESSED record is excluded from the cohort, is named in the excluded set with its "
    "reason, and never becomes an analysed member",
    lambda v: v.get("excluded") == ["ANOM-01"] and v.get("members_include_it") is False,
    body='''
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
recs = [dict(r, qualification_state=("UNASSESSED" if r["project_id"] == "ANOM-01"
                                     else r["qualification_state"]))
        for r in fx["feature_records"]]
c = V8.PortfolioCohort(fx["cohort"], fx["feature_schema"], recs)
emit({"ok": True, "excluded": [m["project_id"] for m in c.excluded],
      "members_include_it": "ANOM-01" in c.project_ids})
''')


# =================================================================================================
head("CAMPAIGN TOTALS")
# =================================================================================================
_data_rows = [r for r in ROWS[1:]]
check(len(_data_rows) == REQUIRED, f"faults required = {REQUIRED}; recorded = {len(_data_rows)}",
      str(len(_data_rows)))
check(APPLIED == REQUIRED, f"applied = {APPLIED}", f"NOT_APPLIED = {REQUIRED - APPLIED}")
check(REDS == REQUIRED, f"intended RED = {REDS}", str(REDS))
check(RESTORED == REQUIRED, f"restored GREEN = {RESTORED}", str(RESTORED))
check(CRASHES == 0, f"crashes accepted as RED = {CRASHES}", str(CRASHES))
ROWS.append(["TOTALS", "-", "-", str(APPLIED), "-", "-", str(REDS), str(CRASHES),
             str(RESTORED), "PASS" if (APPLIED == REDS == RESTORED == REQUIRED
                                       and CRASHES == 0) else "FAIL"])
with OUT.open("w", encoding="utf-8", newline="") as fh:
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
