#!/usr/bin/env python3
"""
RUN 33 FINAL CLOSURE. THE TEN-FAULT NON-VACUITY CAMPAIGN FOR THE PH.1 FIXED-FOREST ORACLE.

A test that cannot fail proves nothing, so every guard the closure rests on is turned RED here by
a real mutation of real production source and then restored.

WHAT A FAULT MUST DO TO COUNT. Baseline GREEN; the mutation APPLIED and CONFIRMED APPLIED by
reading the mutated file back; a NAMED GUARD going RED FOR THE INTENDED REASON; restore; caches
cleared; baseline GREEN again. An exception raised by the mutation is reported as a CRASH and
scored ZERO -- a crash is not a RED.

THE SHAPE TO WATCH FOR, which cost six faults a first pass in the main Run-33 campaign: a
"mutation" that changes only the INPUT while the property genuinely holds is not a fault
injection. Every fault below mutates PRODUCTION SOURCE (or, for fault 10, the oracle itself) so
that the arithmetic or the structure the guard names actually changes.

TWO FAULTS NEEDED CARE AND ARE RECORDED HERE RATHER THAN QUIETLY REPOINTED:

  * FAULT 3 (wrong c(psi) denominator) CANNOT be expressed as "use len(training) instead of psi"
    on the compact ten-point fixture, because there psi = min(256, 10) = 10 = len(training) and
    the two are the SAME NUMBER -- the mutation would apply and change nothing, and the campaign
    would have credited a fault it had not proved. It is expressed as a genuinely wrong
    denominator and exercised on the 300-point fixture where psi = 256 differs from n = 300.

  * FAULT 10 cannot be caught by the equivalence guard at all: an oracle that DELEGATES to
    production agrees with production trivially, so equivalence would stay green. Its guard is
    the independence proof -- perturb production's path length in process and require the
    ORACLE's answer to be UNMOVED. A delegating oracle moves with it.

SOURCE MUTATIONS DROP __pycache__ ON BOTH SIDES: a restore within the same clock second changes
neither mtime nor size, so a cached mutant would survive. Every probe runs in a fresh interpreter
with bytecode writing disabled.

Writes code_audit/run33_ph1_fault_injection_results.csv.
"""

from __future__ import annotations

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

OUT = ROOT / "code_audit" / "run33_ph1_fault_injection_results.csv"
FIXTURES = (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.5"
            / "package_D_portfolio_health")
IF_SRC = "server/app/simulation/isolation_forest.py"
V8_SRC = "server/app/simulation/canonical_v8.py"
ORACLE_SRC = "server/tools/run33_frozen_forest.py"

REQUIRED = 10
PASSED = 0
FAILED = 0
FAILURES: list[str] = []
ROWS: list[list[str]] = [["fault", "target", "mutation", "applied", "confirmed_applied", "guard",
                          "intended_red", "crash_accepted_as_red", "restored_green", "result"]]
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


def run_probe(body: str, arg: str = "") -> dict:
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
    global APPLIED, REDS, RESTORED, CRASHES
    f = ROOT / path
    original = f.read_text(encoding="utf-8")
    drop_pycache()
    base = run_probe(body, arg)
    green_before = check(base.get("ok") is True and guard(base) is True,
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
                red = check(guard(got) is False,
                            f"F{n} RED for the intended reason: {guard_name}",
                            json.dumps({k: v for k, v in got.items() if k != "ok"})[:150])
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


# ---------------------------------------------------------------------------------------------
# THE PROBES
# ---------------------------------------------------------------------------------------------

#: Fixed-forest equivalence over a fixture, reported as the worst absolute difference. `sys.argv[2]`
#: names the fixture, so the arithmetic faults can be exercised where psi differs from n.
EQUIV_PROBE = """
import run33_frozen_forest as O
from app.simulation import canonical_v8 as V8
from app.simulation.isolation_forest import IsolationForest
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
c = V8.PortfolioCohort(fx["cohort"], fx["feature_schema"], fx["feature_records"])
feats = [f for f in c.features if f.required]
X = [[c.value(m, f) for f in feats] for m in c.members]
forest = IsolationForest(X, n_trees=V8.IF_TREES, subsample=min(V8.IF_SUBSAMPLE, len(X)),
                         seed=V8.IF_SEED)
frozen = O.serialize_forest(forest)
ws = max(abs(forest.anomaly_score(x) - O.oracle_score(frozen, x)) for x in X)
wp = 0.0
for x in X:
    a, b = forest.path_lengths(x), O.oracle_path_lengths(frozen, x)
    wp = max(wp, max(abs(u - v) for u, v in zip(a, b)))
emit({"ok": True, "worst_score": ws, "worst_path": wp, "psi": frozen["psi"], "n": len(X)})
"""


def equiv_guard(v):
    import run33_frozen_forest as O
    return (v.get("worst_score", 1.0) <= O.EQUIVALENCE_TOLERANCE
            and v.get("worst_path", 1.0) <= O.EQUIVALENCE_TOLERANCE)


#: The production route: every reported score must be the score ONE forest produces, recomputed
#: independently by the oracle from the model metadata the route itself reported.
ROUTE_PROBE = """
import run33_frozen_forest as O
from app.simulation import canonical_v8 as V8
from app.simulation.isolation_forest import IsolationForest
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
run = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], fx["feature_records"], [])
d = run["results"]["cat8_1_isolation_forest"]
c = V8.PortfolioCohort(fx["cohort"], fx["feature_schema"], fx["feature_records"])
feats = [f for f in c.features if f.required]
X = [[c.value(m, f) for f in feats] for m in c.members]
m = d["model"]
one = IsolationForest(X, n_trees=m["n_trees"], subsample=m["subsample_psi"], seed=m["seed"])
frozen = O.serialize_forest(one)
gap = max(abs(d["projects"][p]["anomaly_score"] - O.oracle_score(frozen, x))
          for p, x in zip(c.project_ids, X))
emit({"ok": True, "gap": gap,
      "population": sorted(m["fitted_project_population"]), "scored": sorted(d["projects"])})
"""


def route_guard(v):
    import run33_frozen_forest as O
    return (v.get("gap", 1.0) <= O.EQUIVALENCE_TOLERANCE
            and v.get("population") == v.get("scored"))


IDENTITY_PROBE = """
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
run = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], fx["feature_records"], [])
d = run["results"]["cat8_1_isolation_forest"]
m = d["model"]
emit({"ok": True, "present": sorted(k for k in
      ("cohort_id", "model_version", "seed", "feature_schema_version")
      if m.get(k) not in (None, "")),
      "cohort_id": d["cohort"].get("cohort_id")})
"""


def identity_guard(v):
    return (v.get("present") == ["cohort_id", "feature_schema_version", "model_version", "seed"]
            and bool(v.get("cohort_id")))


REPRO_PROBE = """
import run33_frozen_forest as O
from app.simulation import canonical_v8 as V8
from app.simulation.isolation_forest import IsolationForest
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
c = V8.PortfolioCohort(fx["cohort"], fx["feature_schema"], fx["feature_records"])
feats = [f for f in c.features if f.required]
X = [[c.value(m, f) for f in feats] for m in c.members]
psi = min(V8.IF_SUBSAMPLE, len(X))
h = [O.forest_digest(O.serialize_forest(
        IsolationForest(X, n_trees=V8.IF_TREES, subsample=psi, seed=V8.IF_SEED)))
     for _ in range(2)]
emit({"ok": True, "same": h[0] == h[1], "digest": h[0][:16]})
"""


def repro_guard(v):
    return v.get("same") is True


FLAG_PROBE = """
from app.simulation import canonical_v8 as V8
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
run = V8.compute_portfolio_health(fx["cohort"], fx["feature_schema"], fx["feature_records"], [])
d = run["results"]["cat8_1_isolation_forest"]
emit({"ok": True,
      "schema": d["cohort"]["feature_schema_version"],
      "frozen_schema": V8.RUN15_FROZEN_SCHEMA,
      "flags": sorted({str(p["exploratory_flag"]) for p in d["projects"].values()})})
"""


def flag_guard(v):
    # The cohort is NOT on the Run-15 frozen schema, so no flag may be derived from the frozen
    # synthetic threshold. Anything other than a bare None is the threshold escaping its schema.
    return v.get("schema") != v.get("frozen_schema") and v.get("flags") == ["None"]


#: THE INDEPENDENCE PROBE. Perturb production's path length IN PROCESS and require the oracle's
#: score to be UNMOVED. This is the only guard fault 10 can be caught by: a delegating oracle
#: agrees with production trivially, so the equivalence guard would stay green.
INDEPENDENCE_PROBE = """
import run33_frozen_forest as O
from app.simulation import canonical_v8 as V8
from app.simulation import isolation_forest as PROD
from app.simulation.isolation_forest import IsolationForest
fx = json.loads(pathlib.Path(sys.argv[2]).read_text())
c = V8.PortfolioCohort(fx["cohort"], fx["feature_schema"], fx["feature_records"])
feats = [f for f in c.features if f.required]
X = [[c.value(m, f) for f in feats] for m in c.members]
forest = IsolationForest(X, n_trees=V8.IF_TREES, subsample=min(V8.IF_SUBSAMPLE, len(X)),
                         seed=V8.IF_SEED)
frozen = O.serialize_forest(forest)
before = O.oracle_score(frozen, X[0])
prod_before = forest.anomaly_score(X[0])
orig = PROD._path_length
PROD._path_length = lambda x, node, depth: orig(x, node, depth) + 1.0
try:
    prod_after = forest.anomaly_score(X[0])
    after = O.oracle_score(frozen, X[0])
finally:
    PROD._path_length = orig
emit({"ok": True, "oracle_moved": abs(after - before) > 1e-12,
      "production_moved": abs(prod_after - prod_before) > 1e-6,
      "oracle_before": before, "oracle_after": after})
"""


def independence_guard(v):
    # Production must move (or the probe proves nothing) and the oracle must NOT.
    return v.get("production_moved") is True and v.get("oracle_moved") is False


PH1 = str(FIXTURES / "ph1_isolation_forest_fixture.json")
RANK = str(FIXTURES / "ph1_rank_agreement_fixture.json")


# =================================================================================================
head("FAULTS 1-5: THE ARITHMETIC INSIDE THE SCORER")
# =================================================================================================
# Exercised on the 300-point fixture, where psi = 256 differs from n = 300 and many terminal nodes
# hold more than one sample -- so a c(psi) or c(n) defect has somewhere to show.

fault(1, "PH.1 isolation_forest._path_length", IF_SRC,
      [("        return _path_length(x, node.left, depth + 1)",
        "        return _path_length(x, node.left, depth + 2)")],
      "the path length counts two edges instead of one when descending left, so h(x) no longer "
      "counts the edges actually traversed",
      "fixed-forest score and per-tree path equivalence with the independent oracle",
      equiv_guard, EQUIV_PROBE, RANK)

fault(2, "PH.1 isolation_forest._path_length", IF_SRC,
      [("        return depth + c_factor(node.size)", "        return depth")],
      "the terminal-node c(n) adjustment is removed, so a node holding several samples is treated "
      "as if it had isolated one",
      "fixed-forest score and per-tree path equivalence with the independent oracle",
      equiv_guard, EQUIV_PROBE, RANK)

fault(3, "PH.1 isolation_forest.IsolationForest", IF_SRC,
      [("        self.normaliser = c_factor(self.subsample)",
        "        self.normaliser = c_factor(self.subsample * 2)")],
      "the score is normalised by c(2*psi) instead of c(psi) -- a genuinely wrong denominator. "
      "NOTE: the natural-looking mutation `c_factor(len(training))` is NOT usable on the compact "
      "fixture, where psi = min(256, 10) = 10 = len(training) and the two are the same number",
      "fixed-forest score equivalence with the independent oracle, which recomputes c(psi) itself",
      equiv_guard, EQUIV_PROBE, RANK)

fault(4, "PH.1 isolation_forest.anomaly_score", IF_SRC,
      [("        return 2.0 ** (-self.mean_path_length(x) / self.normaliser)",
        "        return 2.0 ** (self.mean_path_length(x) / self.normaliser)")],
      "the exponent sign in s(x, psi) = 2 ** (-E[h(x)] / c(psi)) is reversed, so a shorter path "
      "would read as LESS anomalous",
      "fixed-forest score equivalence with the independent oracle",
      equiv_guard, EQUIV_PROBE, RANK)

fault(5, "PH.1 isolation_forest.mean_path_length", IF_SRC,
      [("        pl = self.path_lengths(x)\n        return sum(pl) / len(pl)",
        "        return self.path_lengths(x)[0]")],
      "the ensemble mean E[h(x)] = (1/t) sum h_i(x) is replaced by the FIRST TREE's path length, "
      "so the ensemble stops averaging",
      "fixed-forest score equivalence with the independent oracle",
      equiv_guard, EQUIV_PROBE, RANK)


# =================================================================================================
head("FAULTS 6-9: THE FOREST, THE IDENTITIES, THE SEED AND THE THRESHOLD")
# =================================================================================================
fault(6, "PH.1 canonical_v8.isolation_forest", V8_SRC,
      [("    for m, v in zip(cohort.members, vectors):\n        score = forest.anomaly_score(v)",
        "    for m, v in zip(cohort.members, vectors):\n"
        "        _ref = [w for w in vectors if w is not v]\n"
        "        score = IsolationForest(_ref, n_trees=n_trees,\n"
        "                                subsample=min(subsample, len(_ref)),\n"
        "                                seed=seed).anomaly_score(v)")],
      "each project is scored by its OWN forest fitted on the other projects, so the scores "
      "reported together come from different forests on different scales",
      "the production route's reported scores ARE the scores one forest produces, recomputed "
      "independently by the oracle from the reported model metadata",
      route_guard, ROUTE_PROBE, PH1)

fault(7, "PH.1 canonical_v8.isolation_forest", V8_SRC,
      [('            "model_version": cohort.model_version,\n'
        '            "fitted_project_population": list(cohort.project_ids),',
        '            "model_version": None,\n'
        '            "fitted_project_population": list(cohort.project_ids),')],
      "the model version is dropped from the result, so two scores could be compared without any "
      "way to know they came from the same model",
      "the result retains cohort id, model version, seed and feature schema version",
      identity_guard, IDENTITY_PROBE, PH1)

fault(8, "PH.1 isolation_forest.IsolationForest", IF_SRC,
      [("        rng = random.Random(seed)", "        rng = random.Random()")],
      "the ensemble stops being seeded: the declared seed is still recorded on the model but the "
      "trees are drawn from an unseeded generator",
      "two independent fits of the same cohort under the same seed give an IDENTICAL frozen-forest "
      "digest", repro_guard, REPRO_PROBE, PH1)

fault(9, "PH.1 canonical_v8 frozen synthetic threshold", V8_SRC,
      [("                bool(score >= RUN15_FROZEN_THRESHOLD)\n"
        "                if cohort.schema_version == RUN15_FROZEN_SCHEMA else None),",
        "                bool(score >= RUN15_FROZEN_THRESHOLD)),")],
      "the frozen Run-15 synthetic threshold is applied regardless of feature schema, so a "
      "laboratory threshold fitted on one schema produces flags on another",
      "no exploratory flag is derived from the frozen synthetic threshold under a schema that is "
      "not the one it was fitted on", flag_guard, FLAG_PROBE, PH1)


# =================================================================================================
head("FAULT 10: THE ORACLE ITSELF")
# =================================================================================================
# THE EQUIVALENCE GUARD CANNOT CATCH THIS ONE. An oracle that delegates to production agrees with
# production trivially, so equivalence stays green -- which is exactly why the closure needs the
# independence proof as a separate guard.
fault(10, "the independent scorer (run33_frozen_forest.oracle_path_length)", ORACLE_SRC,
      [("""def oracle_path_length(tree: Mapping[str, Any], x, depth: int = 0) -> float:""",
        """def oracle_path_length(tree: Mapping[str, Any], x, depth: int = 0) -> float:
    from app.simulation.isolation_forest import _Node, _path_length

    def _mk(t):
        if t["external"]:
            return _Node(True, size=t["size"])
        return _Node(False, attribute=t["feature"], split=t["split"],
                     left=_mk(t["left"]), right=_mk(t["right"]))

    return _path_length(x, _mk(tree), depth)""")],
      "the independent scorer is replaced by a call to PRODUCTION's own path-length function, so "
      "it copies the implementation it is supposed to be checking instead of evaluating the "
      "frozen trees itself",
      "with production's path length perturbed in process, the ORACLE's score is UNMOVED while "
      "production's moves -- which only a genuinely independent scorer can satisfy",
      independence_guard, INDEPENDENCE_PROBE, PH1)


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

ROWS.append(["TOTALS", "-", "-", str(APPLIED), "-", "-", str(REDS), str(CRASHES),
             str(RESTORED),
             "PASS" if (APPLIED == REDS == RESTORED == REQUIRED and CRASHES == 0) else "FAIL"])
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
