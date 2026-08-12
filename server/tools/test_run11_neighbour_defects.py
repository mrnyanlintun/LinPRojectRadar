#!/usr/bin/env python3
"""
RUN 11, GATE 3. THE SEVEN REMAINING NEIGHBOUR DEFECTS.

THE SEVEN ARE READ OUT OF THE COMMITTED RUN 10B ARTEFACT, NOT TYPED IN. code_audit/
run10b_neighbour_findings.csv is the record of what that sweep reproduced; the rows with
fixed=no are the seven, and this suite fails if that set is not exactly seven or does not match
the seven it tests. A list retyped from a summary is a list that can drift from the evidence.

TWO INDEPENDENT PROPERTIES, NOT SEVEN HAND-WRITTEN EXPECTATIONS.

  PROPERTY A — DOMAIN CLOSURE. A quantity has a domain that comes from what it is, not from
  where the bands sit: money spent is not negative, a percentage complete is a share of the work,
  a performance index is a ratio of two non-negative quantities. Outside that domain a module
  must produce no status at all. This is checked by RANDOMISED SWEEP over each module's inputs,
  not by the sweep's illustrative case: several hundred out-of-domain draws per module, each
  required to abstain, plus the exact reproducer the Run 10B sweep recorded.

  PROPERTY B — MISSINGNESS IS NEVER AN IMPROVEMENT. For a required input, removing it must not
  yield a calmer band than supplying it. Removing it must yield NO band. This is checked by
  taking in-domain draws that produce a reading, deleting one required field, and requiring the
  result to abstain rather than to move down the ladder.

Neither property mentions a threshold, and neither was derived from the code under test.

MUTATION PROOFS at the end restore each pre-fix behaviour in a live copy of the module function
and require the property to go red. The restoration is asserted to have changed behaviour before
the red is believed, because an injection that silently fails to apply reports a false clean.
"""
from __future__ import annotations

import csv
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation import models_doc, models_evm, models_ext, models_gov  # noqa: E402
from app.simulation.registry import CORE_VOTING_MODULES  # noqa: E402

PASS = 0
TOTAL = 0
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS, TOTAL
    TOTAL += 1
    if ok:
        PASS += 1
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"FAIL  {name}  {detail}")


def rand() -> float:
    return 0.5


def abstains(out: dict) -> bool:
    return bool(out.get("insufficient_data")) and out.get("status_color") is None


#: One entry per defect row in the Run 10B artefact. `base` is an in-domain input set that
#: produces a reading; `domains` names each required field with the predicate its quantity
#: satisfies; `required_for_missingness` names fields whose absence must abstain.
SPECS = {
    ("A1.9", "out-of-domain input reads Green"): {
        "name": "Budget Execution Rate",
        "fn": models_evm.run_budget_execution,
        "base": {"ac": 1_150_000.0, "bac": 1_000_000.0, "actualPctComplete": 80.0},
        "domains": {"ac": (0.0, None), "bac": (0.0, None), "actualPctComplete": (0.0, 100.0)},
        "required": ("ac", "bac", "actualPctComplete"),
        "reproducer": {"ac": -700_000.0, "bac": 1_000_000.0, "actualPctComplete": 50.0},
        "defect_class": "out-of-domain banding",
    },
    ("A2.6", "out-of-domain input reads Green"): {
        "name": "S-Curve Deviation",
        "fn": models_ext.run_scurve_deviation,
        "base": {"actualPctComplete": 40.0, "plannedPctComplete": 55.0,
                 "ev": 400_000.0, "pv": 550_000.0},
        "domains": {"actualPctComplete": (0.0, 100.0), "plannedPctComplete": (0.0, 100.0),
                    "ev": (0.0, None), "pv": (0.0, None)},
        "required": ("actualPctComplete", "plannedPctComplete", "ev", "pv"),
        "reproducer": {"actualPctComplete": 40.0, "plannedPctComplete": -60.0,
                       "ev": 400_000.0, "pv": 550_000.0},
        "defect_class": "out-of-domain banding",
    },
    ("A3.9", "out-of-domain input reads Green"): {
        "name": "Inflation Adjustment Index",
        "fn": models_ext.run_inflation_adjustment,
        "base": {"materialCostBaseline": 500_000.0, "materialCostCurrent": 600_000.0,
                 "actualPctComplete": 80.0},
        "domains": {"materialCostBaseline": (0.0, None), "materialCostCurrent": (0.0, None),
                    "actualPctComplete": (0.0, 100.0)},
        "required": ("materialCostBaseline", "materialCostCurrent", "actualPctComplete"),
        "reproducer": {"materialCostBaseline": 500_000.0, "materialCostCurrent": -100_000.0,
                       "actualPctComplete": 80.0},
        "defect_class": "out-of-domain banding",
    },
    ("A3.9", "removing evidence improves the reading"): {
        "name": "Inflation Adjustment Index",
        "fn": models_ext.run_inflation_adjustment,
        "base": {"materialCostBaseline": 500_000.0, "materialCostCurrent": 600_000.0,
                 "actualPctComplete": 80.0},
        "domains": {},
        "required": ("actualPctComplete",),
        "reproducer": None,
        "defect_class": "missingness improved the reading",
    },
    ("A5.2", "removing evidence improves the reading"): {
        "name": "Sensitivity Analysis",
        "fn": models_doc.run_sensitivity_analysis,
        "base": {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 500_000.0, "pv": 450_000.0,
                 "cpi": 0.8, "spi": 0.89, "docRiskScore": 0.55},
        "domains": {"docRiskScore": (0.0, 1.0)},
        "required": ("docRiskScore",),
        "reproducer": None,
        "defect_class": "missingness improved the reading",
    },
    ("A5.3", "out-of-domain input reads Green"): {
        "name": "Tornado Risk Ranking",
        "fn": models_doc.run_tornado_diagram,
        "base": {"cpi": 0.8, "spi": 0.89, "docRiskScore": 0.55,
                 "actualPctComplete": 40.0, "plannedPctComplete": 55.0},
        "domains": {"docRiskScore": (0.0, 1.0), "cpi": (0.0001, None), "spi": (0.0001, None),
                    "actualPctComplete": (0.0, 100.0), "plannedPctComplete": (0.0, 100.0)},
        "required": ("cpi", "spi", "docRiskScore", "actualPctComplete", "plannedPctComplete"),
        "reproducer": {"cpi": 0.8, "spi": 0.89, "docRiskScore": -30.0,
                       "actualPctComplete": 40.0, "plannedPctComplete": 55.0},
        "defect_class": "out-of-domain banding",
    },
    ("B3.2", "out-of-domain input reads Green"): {
        "name": "FAR Threshold Monitor",
        "fn": models_gov.run_far_threshold,
        "base": {"bac": 1_000_000.0, "cpi": 0.88, "ev": 400_000.0, "ac": 455_000.0},
        "domains": {"cpi": (0.0001, None), "bac": (0.0001, None)},
        "required": ("bac", "cpi", "ev", "ac"),
        "reproducer": {"bac": 1_000_000.0, "cpi": -0.857, "ev": 400_000.0, "ac": 455_000.0},
        "defect_class": "out-of-domain banding",
    },
}


def the_seven_from_the_artefact() -> set[tuple[str, str]]:
    path = ROOT / "code_audit" / "run10b_neighbour_findings.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    return {(r["module_id"], r["defect_class"]) for r in rows if r["fixed"].strip() == "no"}


def reconciliation() -> None:
    seven = the_seven_from_the_artefact()
    check("the Run 10B artefact records exactly seven unfixed neighbour defects",
          len(seven) == 7, f"{len(seven)}: {sorted(seven)}")
    check("the seven tested here are exactly the seven recorded",
          seven == set(SPECS), f"only in artefact {seven - set(SPECS)}; "
                               f"only here {set(SPECS) - seven}")


def reproducers() -> None:
    """The exact case the Run 10B sweep recorded, for each of the five out-of-domain defects."""
    for (mid, cls), spec in SPECS.items():
        if not spec["reproducer"]:
            continue
        out = spec["fn"](dict(spec["reproducer"]), rand, None)
        check(f"{mid} {spec['name']}: the recorded reproducer abstains",
              abstains(out), f"status {out.get('status_color')}")
        check(f"{mid} {spec['name']}: the abstention names why",
              len(out.get("evidence_metric", "")) > 40
              and "substitute" in out.get("evidence_metric", ""),
              out.get("evidence_metric", "")[:80])
        check(f"{mid} {spec['name']}: the abstention carries a machine reason",
              out.get("abstention_reason_code") == "malformed_input",
              str(out.get("abstention_reason_code")))


def property_a_domain_closure() -> None:
    """Randomised: every out-of-domain draw must abstain. 200 draws per field."""
    rng = random.Random(1109)
    for (mid, cls), spec in SPECS.items():
        if not spec["domains"]:
            continue
        for field, (lo, hi) in spec["domains"].items():
            bad = 0
            for _ in range(200):
                si = dict(spec["base"])
                if rng.random() < 0.5 or hi is None:
                    v = lo - rng.uniform(0.001, 5_000_000.0)
                else:
                    v = hi + rng.uniform(0.001, 5_000_000.0)
                si[field] = v
                if not abstains(spec["fn"](si, rand, None)):
                    bad += 1
            check(f"{mid} {spec['name']}: 200 out-of-domain draws of {field} all abstain",
                  bad == 0, f"{bad} produced a band")
        # ...and the in-domain base still produces a reading, so the module has not been
        # silenced altogether. A guard that refuses everything is not a correction.
        out = spec["fn"](dict(spec["base"]), rand, None)
        check(f"{mid} {spec['name']}: the in-domain case still reports",
              out.get("status_color") in ("Green", "Yellow", "Amber", "Red"),
              str(out.get("status_color")))


def property_b_missingness() -> None:
    """Deleting a required field must abstain, never produce a calmer band."""
    for (mid, cls), spec in SPECS.items():
        for field in spec["required"]:
            si = dict(spec["base"])
            si.pop(field, None)
            out = spec["fn"](si, rand, None)
            check(f"{mid} {spec['name']}: removing {field} abstains rather than re-bands",
                  abstains(out), f"status {out.get('status_color')}")
        # and explicitly None, which is how an unreported field arrives
        for field in spec["required"]:
            si = dict(spec["base"])
            si[field] = None
            out = spec["fn"](si, rand, None)
            check(f"{mid} {spec['name']}: {field} reported as nothing abstains",
                  abstains(out), f"status {out.get('status_color')}")


def boundaries() -> None:
    """The domain edges themselves, which are in-domain and must still report."""
    edges = [
        # ac exactly 0 abstains for a reason that predates this run and is not touched here:
        # a zero execution rate is the JS `!executionRate` fallthrough, refused since Run 7. The
        # smallest positive actual cost is the domain edge this run is responsible for.
        ("A1.9", models_evm.run_budget_execution,
         {"ac": 1.0, "bac": 1_000_000.0, "actualPctComplete": 100.0}, True),
        ("A2.6", models_ext.run_scurve_deviation,
         {"actualPctComplete": 0.0, "plannedPctComplete": 0.0, "ev": 0.0, "pv": 550_000.0}, True),
        ("A3.9", models_ext.run_inflation_adjustment,
         {"materialCostBaseline": 500_000.0, "materialCostCurrent": 0.0,
          "actualPctComplete": 100.0}, True),
        ("A5.3", models_doc.run_tornado_diagram,
         {"cpi": 1.0, "spi": 1.0, "docRiskScore": 0.0, "actualPctComplete": 0.0,
          "plannedPctComplete": 0.0}, True),
        ("A5.3", models_doc.run_tornado_diagram,
         {"cpi": 1.0, "spi": 1.0, "docRiskScore": 1.0, "actualPctComplete": 100.0,
          "plannedPctComplete": 100.0}, True),
        ("B3.2", models_gov.run_far_threshold,
         {"bac": 1_000_000.0, "cpi": 1.0, "ev": 400_000.0, "ac": 400_000.0}, True),
    ]
    for mid, fn, si, should_report in edges:
        out = fn(dict(si), rand, None)
        check(f"{mid}: the domain edge {si} is inside the domain and reports",
              (out.get("status_color") is not None) == should_report,
              f"status {out.get('status_color')}, {out.get('evidence_metric', '')[:60]}")


def voting_unchanged() -> None:
    check("the voting set is exactly two", set(CORE_VOTING_MODULES) == {"A1.7", "A1.8"},
          str(sorted(CORE_VOTING_MODULES)))
    for mid, _cls in SPECS:
        check(f"{mid} did not become voting", mid not in CORE_VOTING_MODULES, "it votes")


def mutation_proofs() -> None:
    """
    THE PRE-FIX BEHAVIOUR IS THE REAL PRE-FIX BEHAVIOUR, not an approximation of it. Each module
    file is read out of the pinned commit that Run 10B left behind and executed in its own
    namespace, so the functions called below are the ones that shipped, with their own guards,
    bands and helpers. Without this the suite would compare the fix with itself and report clean.

    Pinned BY SHA rather than by branch name: once this run merges, origin/main becomes this code.
    """
    import subprocess
    import types

    baseline_rev = "68fe615"

    def baseline_module(name: str):
        src = subprocess.run(
            ["git", "show", f"{baseline_rev}:server/app/simulation/{name}.py"],
            cwd=str(ROOT), capture_output=True, text=True, check=True).stdout
        mod = types.ModuleType(f"baseline_{name}")
        mod.__package__ = "app.simulation"
        mod.__name__ = f"app.simulation.{name}"
        exec(compile(src, f"<{baseline_rev}:{name}>", "exec"), mod.__dict__)
        return mod, src

    cases = [
        ("A1.9", "models_evm", "run_budget_execution",
         {"ac": -700_000.0, "bac": 1_000_000.0, "actualPctComplete": 50.0}),
        ("A2.6", "models_ext", "run_scurve_deviation",
         {"actualPctComplete": 40.0, "plannedPctComplete": -60.0, "ev": 400_000.0,
          "pv": 550_000.0}),
        ("A3.9", "models_ext", "run_inflation_adjustment",
         {"materialCostBaseline": 500_000.0, "materialCostCurrent": -100_000.0,
          "actualPctComplete": 80.0}),
        ("A5.3", "models_doc", "run_tornado_diagram",
         {"cpi": 0.8, "spi": 0.89, "docRiskScore": -30.0, "actualPctComplete": 40.0,
          "plannedPctComplete": 55.0}),
        ("B3.2", "models_gov", "run_far_threshold",
         {"bac": 1_000_000.0, "cpi": -0.857, "ev": 400_000.0, "ac": 455_000.0}),
    ]
    live_modules = {"models_evm": models_evm, "models_ext": models_ext,
                    "models_doc": models_doc, "models_gov": models_gov}
    for mid, modname, fname, si in cases:
        baseline, src = baseline_module(modname)
        live_src = (ROOT / "server" / "app" / "simulation" / f"{modname}.py").read_text(
            encoding="utf-8")
        check(f"MUTATION {mid}: the pinned baseline source differs from the live source",
              src != live_src, "identical, so nothing was corrected")
        before = getattr(baseline, fname)(dict(si), rand, None)
        after = getattr(live_modules[modname], fname)(dict(si), rand, None)
        check(f"MUTATION RED {mid}: the shipped pre-fix function banded the reproducer",
              before.get("status_color") == "Green",
              f"it read {before.get('status_color')}")
        check(f"MUTATION {mid}: the corrected function abstains on the same input",
              abstains(after), f"status {after.get('status_color')}")

    # The two missingness corrections, against the same pinned baseline.
    b_ext, _ = baseline_module("models_ext")
    # The case the Run 10B sweep recorded: with progress supplied the escalation is measured
    # above a baseline scaled to 90 per cent of the work and reads Red; with progress withheld
    # the full baseline is the denominator, the same overspend reads 10 per cent, and the module
    # returns Amber. Removing evidence bought a calmer band.
    base = {"materialCostBaseline": 500_000.0, "materialCostCurrent": 550_000.0}
    before = b_ext.run_inflation_adjustment(dict(base), rand, None)
    after = models_ext.run_inflation_adjustment(dict(base), rand, None)
    check("MUTATION RED A3.9 missingness: the pre-fix function banded with progress absent",
          before.get("status_color") is not None, "it abstained anyway")
    with_progress = b_ext.run_inflation_adjustment(dict(base, actualPctComplete=90.0), rand, None)
    order = ["Green", "Yellow", "Amber", "Red"]
    check("MUTATION RED A3.9 missingness: and removing progress made the reading calmer",
          order.index(before["status_color"]) < order.index(with_progress["status_color"]),
          f"{with_progress.get('status_color')} -> {before.get('status_color')}")
    check("A3.9 missingness: corrected, absent progress abstains",
          abstains(after), f"status {after.get('status_color')}")
    check("A3.9 missingness: corrected, supplied progress still reports",
          models_ext.run_inflation_adjustment(
              dict(base, actualPctComplete=90.0), rand, None).get("status_color") is not None,
          "it abstained too")

    b_doc, _ = baseline_module("models_doc")
    s_base = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 500_000.0, "pv": 450_000.0,
              "cpi": 0.8, "spi": 0.89}
    before = b_doc.run_sensitivity_analysis(dict(s_base), rand, None)
    with_doc_before = b_doc.run_sensitivity_analysis(dict(s_base, docRiskScore=0.55), rand, None)
    after = models_doc.run_sensitivity_analysis(dict(s_base), rand, None)
    check("MUTATION RED A5.2 missingness: the pre-fix function banded with the driver absent",
          before.get("status_color") is not None, "it abstained anyway")
    check("MUTATION RED A5.2 missingness: and removing the driver made the reading calmer",
          order.index(before["status_color"]) < order.index(with_doc_before["status_color"]),
          f"{with_doc_before.get('status_color')} -> {before.get('status_color')}")
    check("A5.2 missingness: corrected, the absent driver abstains",
          abstains(after), f"status {after.get('status_color')}")
    with_doc = models_doc.run_sensitivity_analysis(dict(s_base, docRiskScore=0.55), rand, None)
    check("A5.2 missingness: corrected, the supplied driver still reports",
          with_doc.get("status_color") is not None, "it abstained too")
    check("A5.2: and the supplied driver can be the top one, which is what zero suppressed",
          with_doc.get("top_driver") == "DocRisk", str(with_doc.get("top_driver")))


reconciliation()
reproducers()
property_a_domain_closure()
property_b_missingness()
boundaries()
voting_unchanged()
mutation_proofs()

print("")
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print("  " + f)
print(f"RESULT: {PASS}/{TOTAL} checks passed")
sys.exit(0 if PASS == TOTAL else 1)
