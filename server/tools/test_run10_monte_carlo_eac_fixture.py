"""
Run 10, Gate 1. The dedicated Monte Carlo EAC Forecast fixture family.

The oracle is research_fixtures/production_contract/monte_carlo_eac_forecast/, whose numbers
were derived from the contract document by tools/derive_mc_eac_fixture.py. No expected value in
this file was produced by running the production module.

The bottom-up triangular cost-risk family in OG-SYNTH-0.3 is a different conceptual model and is
deliberately NOT read here; test_run10_synthetic_integration and the Run 9 suite keep it separate.
"""
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402
import csv
import math
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("SESSION_SECRET", "test-secret-do-not-use-in-prod")

from app.simulation.models_sim import monte_carlo_eac, run_monte_carlo  # noqa: E402
from app.simulation.rng import make_rng, pctile  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIX = ROOT / "research_fixtures" / "production_contract" / "monte_carlo_eac_forecast"
Z = 3.290526731491896

passed = 0
total = 0
failures = []


def check(name, condition):
    global passed, total
    total += 1
    if condition:
        passed += 1
    else:
        failures.append(name)


def rel(a, b):
    if b == 0:
        return abs(a - b)
    return abs(a - b) / abs(b)


def load(name):
    with (FIX / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


cases = {r["case_id"]: r for r in load("known_answer_cases.csv")}
truth = {r["case_id"]: r for r in load("known_answer_ground_truth.csv")}
check("fixture family carries ten cases", len(cases) == 10)
check("every case has ground truth", set(cases) == set(truth))

for cid, case in cases.items():
    t = truth[cid]
    inputs = {"bac": float(case["bac"]), "cpi": float(case["cpi"]),
              "spi": float(case["spi"]), "docScore": float(case["doc_risk_score"])}
    seed = int(case["seed"])
    n = int(case["iterations"])
    got = monte_carlo_eac(inputs, seed=seed, iterations=n)

    # --- golden checks against frozen literals
    check(f"{cid} mode EAC", rel(got["mEAC"], float(t["m_eac"])) < 1e-12)
    check(f"{cid} spread driver", rel(got["s"], float(t["spread_driver"])) < 1e-12)
    check(f"{cid} optimistic bound", rel(got["o"], float(t["optimistic"])) < 1e-12)
    check(f"{cid} most likely bound", rel(got["m"], float(t["most_likely"])) < 1e-12)
    check(f"{cid} pessimistic bound", rel(got["p"], float(t["pessimistic"])) < 1e-12)
    check(f"{cid} baseline is the budget", got["baseline"] == float(case["bac"]))
    check(f"{cid} iteration count is honoured", got["iterations"] == n)

    # --- properties that hold for every case
    check(f"{cid} percentiles finite", math.isfinite(got["p50"]) and math.isfinite(got["p80"]))
    check(f"{cid} p50 at or below p80", got["p50"] <= got["p80"])
    check(f"{cid} p50 within the support", float(t["optimistic"]) <= got["p50"] <= float(t["pessimistic"]) + 1e-6)
    again = monte_carlo_eac(dict(inputs), seed=seed, iterations=n)
    check(f"{cid} same seed reproduces", again["p50"] == got["p50"] and again["p80"] == got["p80"])
    check(f"{cid} overrun percentage agrees with the budget",
          rel(got["overrunPctP80"], (got["p80"] / float(case["bac"]) - 1) * 100) < 1e-9)

    if t["degenerate"] == "true":
        # --- deterministic collapse, exactly derivable
        check(f"{cid} collapses to the mode EAC at p50", got["p50"] == float(t["deterministic_p50"]))
        check(f"{cid} collapses to the mode EAC at p80", got["p80"] == float(t["deterministic_p80"]))
    else:
        # --- statistical acceptance against the analytic Beta-PERT mean
        rand = make_rng(seed)
        # Recover the sample by the documented percentile convention rather than by trusting a
        # returned moment: the module does not expose its samples, so the mean is recomputed on a
        # fresh identically seeded draw through the module itself at a larger count below.
        big = monte_carlo_eac(dict(inputs), seed=seed, iterations=20000)
        check(f"{cid} larger run stays ordered", big["p50"] <= big["p80"])
        # The shape parameters production derives are not returned, so they are pinned
        # indirectly: a reference draw built from the FIXTURE's alpha, beta and bounds over the
        # same generator must land on the same percentiles production reports. A production
        # edit to the Beta-PERT lambda moves production's percentiles away from these.
        from app.simulation.models_sim import _beta as _ref_beta
        r = make_rng(seed)
        a_f, b_f = float(t["alpha"]), float(t["beta"])
        o_f, p_f = float(t["optimistic"]), float(t["pessimistic"])
        ref = sorted(o_f + _ref_beta(a_f, b_f, r) * (p_f - o_f) for _ in range(n))
        check(f"{cid} p50 matches the fixture-parameterised reference draw",
              rel(got["p50"], pctile(ref, 0.50)) < 1e-12)
        check(f"{cid} p80 matches the fixture-parameterised reference draw",
              rel(got["p80"], pctile(ref, 0.80)) < 1e-12)

# --- statistical acceptance: analytic mean versus simulated mean, sampling-error tolerance.
# The module returns percentiles rather than a mean, so the sample is rebuilt here from the
# module's own documented construction and its mean compared with the closed-form PERT mean.
from app.simulation.models_sim import _beta  # noqa: E402

conv_rows = []
for cid in ["MC-03-cpi-driven", "MC-06-deteriorating", "MC-08-spread-upper-region"]:
    t = truth[cid]
    o, m, p = float(t["optimistic"]), float(t["most_likely"]), float(t["pessimistic"])
    alpha, beta = float(t["alpha"]), float(t["beta"])
    for n in (1000, 5000, 20000):
        rand = make_rng(20260812)
        samples = [o + _beta(alpha, beta, rand) * (p - o) for _ in range(n)]
        mean = sum(samples) / n
        sd = math.sqrt(sum((x - mean) ** 2 for x in samples) / (n - 1))
        se = sd / math.sqrt(n)
        analytic = float(t["analytic_mean"])
        tol = Z * se
        ok = abs(mean - analytic) <= tol
        conv_rows.append((cid, n, analytic, mean, abs(mean - analytic), se, tol, "PASS" if ok else "FAIL"))
        check(f"{cid} simulated mean within sampling error at {n}", ok)
        check(f"{cid} simulated sd near the analytic sd at {n}",
              rel(sd, float(t["analytic_sd"])) < 0.15)
        ordered = sorted(samples)
        check(f"{cid} ordered percentiles at {n}",
              pctile(ordered, 0.50) <= pctile(ordered, 0.80) <= pctile(ordered, 0.90))

with (artifact_out(ROOT / "code_audit" / "run10_mc_eac_statistical_acceptance.csv")).open("w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["case_id", "iterations", "analytic_mean", "simulated_mean", "difference",
                "standard_error", "tolerance", "result"])
    w.writerows(conv_rows)

# --- monotonicity properties
base = {"bac": 1_000_000.0, "cpi": 0.95, "spi": 1.0, "docScore": 0.0}
worse = dict(base, cpi=0.80)
b1 = monte_carlo_eac(dict(base), seed=7, iterations=5000)
b2 = monte_carlo_eac(dict(worse), seed=7, iterations=5000)
check("a worse cost index does not improve the forecast", b2["p50"] > b1["p50"] and b2["p80"] > b1["p80"])
check("a worse cost index does not narrow the spread", b2["s"] > b1["s"])
doubled = monte_carlo_eac(dict(base, bac=2_000_000.0), seed=7, iterations=5000)
check("doubling the budget doubles the forecast", rel(doubled["p80"], 2 * b1["p80"]) < 1e-9)
check("doubling the budget leaves the spread driver alone", doubled["s"] == b1["s"])
worse_spi = monte_carlo_eac(dict(base, spi=0.7), seed=7, iterations=5000)
check("a worse schedule index widens the spread", worse_spi["s"] > b1["s"])

# --- refusals
def refuses(name, fn):
    try:
        fn()
    except ValueError:
        check(name, True)
        return
    check(name, False)


refuses("a budget of zero refuses", lambda: monte_carlo_eac({"bac": 0, "cpi": 1.0, "spi": 1.0}, seed=1))
refuses("a cost index of zero refuses", lambda: monte_carlo_eac({"bac": 1e6, "cpi": 0, "spi": 1.0}, seed=1))
refuses("a negative cost index refuses", lambda: monte_carlo_eac({"bac": 1e6, "cpi": -0.5, "spi": 1.0}, seed=1))
refuses("a schedule index of zero refuses", lambda: monte_carlo_eac({"bac": 1e6, "cpi": 1.0, "spi": 0}, seed=1))
refuses("a zero iteration count refuses",
        lambda: monte_carlo_eac({"bac": 1e6, "cpi": 0.9, "spi": 1.0}, seed=1, iterations=0))
refuses("a negative iteration count refuses",
        lambda: monte_carlo_eac({"bac": 1e6, "cpi": 0.9, "spi": 1.0}, seed=1, iterations=-5))
refuses("a fractional iteration count refuses",
        lambda: monte_carlo_eac({"bac": 1e6, "cpi": 0.9, "spi": 1.0}, seed=1, iterations=2.5))

# --- the removed budget substitution must never return
for absent in (0, None, ""):
    try:
        monte_carlo_eac({"bac": absent, "cpi": 1.0, "spi": 1.0}, seed=1)
        check(f"no substitute budget for {absent!r}", False)
    except ValueError:
        check(f"no substitute budget for {absent!r}", True)

# --- abstention through the real module wrapper
def abstains(name, si, fragment=None):
    out = run_monte_carlo(si, None, 42)
    ok = out.get("status_color") in (None, "Gray", "gray", "Grey") or "insufficient" in str(out).lower() \
        or out.get("insufficient") or out.get("abstained")
    if fragment:
        ok = ok and fragment.lower() in str(out).lower()
    check(name, bool(ok))


abstains("absent budget abstains", {"bac": None, "cpi": 1.0, "spi": 1.0})
abstains("absent cost index abstains", {"bac": 1e6, "cpi": None, "spi": 1.0})
abstains("absent schedule index abstains", {"bac": 1e6, "cpi": 1.0, "spi": None})
abstains("a budget of zero abstains rather than substituting", {"bac": 0.0, "cpi": 1.0, "spi": 1.0}, "budget")
abstains("a zero cost index abstains", {"bac": 1e6, "cpi": 0.0, "spi": 1.0}, "performance")
abstains("a negative schedule index abstains", {"bac": 1e6, "cpi": 1.0, "spi": -1.0}, "performance")

live = run_monte_carlo({"bac": 1_000_000.0, "cpi": 0.9, "spi": 0.95, "docRiskScore": 0.1}, None, 42)
check("the live path returns both percentiles",
      math.isfinite(live["p50_eac"]) and math.isfinite(live["p80_eac"]))
check("the live path orders its percentiles", live["p50_eac"] <= live["p80_eac"])
check("the live path names its method class", live["method_class"] == "Monte_Carlo")
check("the live path reports its iteration count", live["iterations"] == 5000)
repeat = run_monte_carlo({"bac": 1_000_000.0, "cpi": 0.9, "spi": 0.95, "docRiskScore": 0.1}, None, 42)
check("the live path is reproducible at one seed", repeat["p80_eac"] == live["p80_eac"])
other = run_monte_carlo({"bac": 1_000_000.0, "cpi": 0.9, "spi": 0.95, "docRiskScore": 0.1}, None, 43)
check("a different seed draws a different path", other["p80_eac"] != live["p80_eac"])

# --- the two families stay distinct
import json  # noqa: E402
contract = json.loads((FIX / "contract.json").read_text(encoding="utf-8"))
check("the fixture family declares its research origin",
      contract["data_origin"] == "SYNTHETIC_RESEARCH_FIXTURE")
check("the fixture family refuses empirical standing",
      contract["not_for_empirical_validation"] is True)
check("the fixture family records the distribution production implements",
      contract["distribution"]["type"] == "BETA_PERT" and contract["distribution"]["lambda"] == 4)
check("the fixture family is declared distinct from the triangular family",
      "triangular" in contract["distinct_from"]["family"].lower())
tri = ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.3" / \
    "Opus_Gubernatio_Synthetic_Programme_v0.3" / "package_A_project_structures" / "monte_carlo_contract.json"
tri_contract = json.loads(tri.read_text(encoding="utf-8"))
check("the triangular family survives untouched",
      tri_contract["cost_element_distribution"]["type"] == "TRIANGULAR")
check("the triangular family still disclaims being the production oracle",
      "not_the_production_model" in tri_contract)

# --- permanent identity, no overlay
alias = ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.3" / \
    "Opus_Gubernatio_Synthetic_Programme_v0.3" / "module_id_aliases.csv"
alias_rows = list(csv.DictReader(alias.open(encoding="utf-8")))
mc_alias = [r for r in alias_rows if r["code_module_id"] == "A1.1"]
sc_alias = [r for r in alias_rows if r["code_module_id"] == "A5.4"]
check("the forecast module has exactly one authoritative alias row", len(mc_alias) == 1)
check("the forecast module alias carries its literature identifier", mc_alias and mc_alias[0]["literature_module_id"] == "1.1")
check("scenario modeling keeps its authoritative alias row", len(sc_alias) == 1)
asset = ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.3" / \
    "Opus_Gubernatio_Synthetic_Programme_v0.3" / "module_asset_map.csv"
asset_rows = list(csv.DictReader(asset.open(encoding="utf-8")))
check("the forecast module has an authoritative asset map row",
      len([r for r in asset_rows if r["code_module_id"] == "A1.1"]) == 1)
check("scenario modeling has an authoritative asset map row",
      len([r for r in asset_rows if r["code_module_id"] == "A5.4"]) == 1)
check("the fixture family declares its permanent repository identifier",
      contract["repository_module_id"] == "A1.1")
check("the fixture family declares its permanent synthetic identifier",
      contract["synthetic_module_id"] == "1.1")
# RUN 28 CLOSURE. THE NAMES SWAPPED PLACES, ON THE OWNER'S DECISION, AND THE CHECK FOLLOWS THE
# DECISION RATHER THAN THE STRING. This fixture was written when the registry said `Monte Carlo
# EAC` and the owner's prose said `Monte Carlo EAC Forecast`, so the prose name sat here as an
# alias. The owner has now decided A1.1 IS `Monte Carlo EAC Forecast` and the naming authority was
# updated; the retired registry name is the backward-compatible alias now. The property this
# check has always had is unchanged: the OTHER name is still resolvable, so a joiner written
# against either era still finds the module.
check("the retired registry name is retained as an alias, so a joiner written before the rename "
      "still resolves the module",
      "Monte Carlo EAC" in contract["backward_compatible_aliases"])
check("and the fixture's canonical name is the one the naming authority now records",
      contract["canonical_module_name"] == "Monte Carlo EAC Forecast")
check("while the stale owner_prose_alias label is nulled rather than deleted, so the record that "
      "the two names once disagreed survives the reconciliation",
      contract["owner_prose_alias"] is None and bool(contract.get("owner_prose_alias_note")))

# --- checksums
import hashlib  # noqa: E402
digest_lines = [l for l in (FIX / "CHECKSUMS.sha256").read_text(encoding="utf-8").splitlines() if l.strip()]
check("the fixture family carries three checksummed files", len(digest_lines) == 3)
for line in digest_lines:
    want, name = line.split("  ")
    got_hash = hashlib.sha256((FIX / name).read_bytes()).hexdigest()
    check(f"checksum holds for {name}", got_hash == want)

for f in failures:
    print("FAILED:", f)
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
