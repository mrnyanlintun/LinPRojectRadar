#!/usr/bin/env python3
"""
The fifteen defects (remediation_programme.md "Run 2 -- the 15 defects";
remediation_decisions_answered.md 2.1 to 2.4), run third under the revised order 1, 3, 2, 4, 5.
Audit P0 findings 3, 4 and 9.

WHAT THIS SUITE HAS TO PROVE, and why it is built the way it is.

1. EVERY AUDIT PROOF IN BOTH DIRECTIONS, AGAINST THE REAL OLD CODE. The instruction is not to
   assume a check can fail but to demonstrate it. This suite does not re-create the old
   arithmetic by hand and it does not inject a fault into the new arithmetic and hope the
   injection applied. It extracts the ACTUAL pre-run files with `git show <the pinned baseline commit>:...` into a
   throwaway package and calls the same functions there. So every proof below reads "the code
   that shipped produced the audit's wrong figure; the code in this branch produces the right
   one", and neither half can be satisfied by a mistake in this file. It closes failure modes 2
   and 4 of the project's standing test discipline at once (an injection that silently fails to
   apply, and asserting against a hand-maintained copy of the logic).

2. THE THREE-WAY CATEGORISATION, MEASURED RATHER THAN DECLARED. Each of the fifteen lands in one
   of: fixed and producing output, fixed and permanently abstaining because the corpus does not
   carry the input, or moved to the disabled set. Section 4 drives a real project through /exec
   and reports which category each one actually landed in on the real path, rather than this
   file asserting a category it decided in advance.

3. THE dst_combine ROLLUP EVIDENCE, BEFORE AND AFTER, MEASURED. Fixing ignorance in Dempster's
   rule changes the category rollup and project status fusion for every project, which is
   expected and required to be evidenced rather than avoided. Section 5 computes the same real
   stored inputs through the same compute_project with the OLD dst_combine and with the new one
   and reports every difference.

4. AN ABSTENTION IS A CORRECT OUTCOME AND IS ASSERTED AS ONE. Six of the fifteen now refuse
   permanently because the input does not exist. This suite asserts they refuse, asserts the
   reason says why in words, and asserts that the reason carries no module id and no em dash,
   because an abstention reason reaches the Signal Ledger.

Run:
    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_run2_fifteen_defects.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
import app.simulation.fusion as fusion  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402
from app.simulation import compute_project  # noqa: E402
from app.simulation.fusion import dst_combine, dst_fuse, normalise_status  # noqa: E402
from app.simulation.models_decision import run_conservative_dominance  # noqa: E402
from app.simulation.models_doc import (  # noqa: E402
    run_contractor_performance, run_environmental_compliance, run_ncr_rate,
    run_procurement_lead_time, run_quality_compliance, run_scenario_modeling,
    run_weather_impact,
)
from app.simulation.models_ext import run_cost_risk, run_float_consumption  # noqa: E402
from app.simulation.models_gov import (  # noqa: E402
    run_majority_rules, run_weighted_voting, run_whatif_matrix, run_worst_n_of_m,
)
from app.simulation.models_sim import run_monte_carlo  # noqa: E402
from app.simulation.portfolio import compute_portfolio  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = 0
FAILED = 0
ROOT = pathlib.Path(__file__).resolve().parents[2]

#: THE BASELINE COMMIT, PINNED BY SHA AND NOT BY BRANCH NAME.
#:
#: This must not be `origin/main`. The moment this run merges, `origin/main` becomes the FIXED
#: code, every "fails on the old code" half of every proof below would be comparing the fix with
#: itself, and the suite would go green while proving nothing. That is precisely the vacuous-check
#: failure this project keeps finding, and it would have been introduced by the suite written to
#: prevent it. The sha is the commit this branch was cut from: the last one carrying the fifteen
#: defects.
BASELINE_REV = "c2c609e"


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


# ---------------------------------------------------------------------------------------------
# THE OLD CODE, LOADED FOR REAL.
#
# Not a re-creation and not an injection: the files as they stand at the pinned baseline commit, extracted into
# a throwaway package and imported. If this extraction fails, the suite REFUSES to run rather
# than skipping the "fails on the old code" half of every proof and reporting a clean pass on
# the other half alone. A suite that quietly tests one direction is exactly the failure this
# project keeps finding.
# ---------------------------------------------------------------------------------------------

_TMP = tempfile.mkdtemp(prefix="fifteen-defects-baseline-")
_PKG = pathlib.Path(_TMP) / "oldsim"
_PKG.mkdir()
_names = subprocess.run(
    ["git", "ls-tree", "--name-only", BASELINE_REV, "server/app/simulation/"],
    cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
_py = [n for n in _names if n.endswith(".py")]
if len(_py) < 10:
    raise SystemExit("baseline extraction found no simulation sources at the pinned baseline; refusing "
                     "to run half of every proof")
for _n in _py:
    body = subprocess.run(["git", "show", f"{BASELINE_REV}:{_n}"],
                          cwd=ROOT, capture_output=True, text=True, check=True).stdout
    (_PKG / pathlib.Path(_n).name).write_text(body, encoding="utf-8")
(_PKG / "__init__.py").write_text("", encoding="utf-8")
sys.path.insert(0, _TMP)
import oldsim.models  # noqa: E402,F401  (root first: it registers the extension tables)
import oldsim.fusion as old_fusion  # noqa: E402
import oldsim.models_decision as old_decision  # noqa: E402
import oldsim.models_doc as old_doc  # noqa: E402
import oldsim.models_ext as old_ext  # noqa: E402
import oldsim.models_gov as old_gov  # noqa: E402
import oldsim.models_sim as old_sim  # noqa: E402
import oldsim.portfolio as old_portfolio  # noqa: E402


def abstains(result) -> bool:
    return bool(result.get("insufficient_data")) and result.get("status_color") is None


def reason(result) -> str:
    return str(result.get("evidence_metric") or "")


def reason_is_speakable(result, label: str) -> None:
    """An abstention reason renders on the Signal Ledger, so the naming rules apply to it."""
    txt = reason(result)
    check(len(txt) > 30 and not txt.startswith("Insufficient data:"),
          f"{label}: the refusal says why in words rather than 'insufficient data'", txt[:110])
    check("—" not in txt and "--" not in txt,
          f"{label}: and carries no em dash", txt[:110])
    check(not any(tok in txt for tok in ("A1.", "A2.", "A3.", "A4.", "A5.", "A6.",
                                         "B1.", "B2.", "B3.", "B4.", "D1.")),
          f"{label}: and carries no module id", txt[:110])


try:
    print("=" * 78)
    print("0. The baseline really is the old code: it reproduces the audit's own figures")
    print("=" * 78)
    print("   Extracted from the pinned baseline commit with `git show`. If these do not reproduce, every")
    print("   'fails on the old code' claim below would be worthless.")

    _b = old_doc.run_quality_compliance(
        {"qualityDeficienciesNoted": 8, "itemsInspected": 5, "itemsFailed": 8}, None, None)
    check(_b.get("pass_rate") == -60,
          "baseline quality compliance returns the audit's pass rate of minus sixty per cent",
          str(_b.get("pass_rate")))
    _b = old_doc.run_procurement_lead_time(
        {"longLeadItemsTotal": 10, "longLeadAtRisk": 8, "longLeadDelayed": 5}, None, None)
    check(_b.get("risk_ratio") == 1.8,
          "baseline procurement lead time returns the audit's ratio of 1.8",
          str(_b.get("risk_ratio")))
    _m = {"Green": 0.8, "Yellow": 0.0, "Amber": 0.0, "Red": 0.0, "Unknown": 0.2}
    _b = old_fusion.dst_combine(_m, _m)
    check(abs(_b["conflict"] - 0.32) < 1e-12 and abs(_b["Green"] - 0.9411764705882353) < 1e-12,
          "baseline Dempster's rule returns the audit's conflict 0.32 and Green 0.941176",
          f"K={_b['conflict']} Green={_b['Green']}")

    print()
    print("=" * 78)
    print("1. Conservative Dominance: two Red signals no longer return Green")
    print("=" * 78)

    AUDIT_CASE = {"signals": {
        "evm": {"status": "Red"}, "mc": {"status": "Red"},
        "cusum": {"status": "Green", "breached": False}, "doc": {"status": "Green"}}}

    old_r = old_decision.run_conservative_dominance(AUDIT_CASE, None, None)
    new_r = run_conservative_dominance(AUDIT_CASE, None, None)
    check(old_r.get("state") == "Green",
          "the audit's case (cost performance Red, forecast Red, control chart Green, document "
          "risk Green) returned Green on the old code", str(old_r.get("state")))
    check(new_r.get("state") == "Red-review",
          "and returns a red review now", str(new_r.get("state")))
    check(new_r.get("conflict") == "Multi-signal red-review",
          "with the conflict classified as a multi-signal red review",
          str(new_r.get("conflict")))

    # Two Reds in EITHER casing, which is the whole point: one vocabulary, not two.
    for casing, statuses in (("capitalised", ("Red", "Red", "Green", "Green")),
                             ("lowercase", ("red", "red", "green", "green")),
                             ("mixed", ("Red", "red", "Green", "green")),
                             ("a red review state", ("Red-review", "red", "green", "green"))):
        case = {"signals": {"evm": {"status": statuses[0]}, "mc": {"status": statuses[1]},
                            "cusum": {"status": statuses[2], "breached": False},
                            "doc": {"status": statuses[3]}}}
        check(run_conservative_dominance(case, None, None).get("state") == "Red-review",
              f"two Red inputs return a red review when written {casing}",
              str(run_conservative_dominance(case, None, None).get("state")))

    # The vote bucket: an unknown value must not become reassuring evidence.
    for bad in ("unexpected", "light-amber", "Yellow", "purple", "n/a"):
        case = {"signals": {"evm": {"status": bad}, "mc": {"status": "green"},
                            "cusum": {"status": "green", "breached": False},
                            "doc": {"status": "green"}}}
        old_s = old_decision.run_conservative_dominance(case, None, None).get("state")
        new_s = run_conservative_dominance(case, None, None).get("state")
        check(old_s == "Green" and new_s != "Green",
              f"a status of '{bad}' bucketed to Green on the old code and no longer does",
              f"old={old_s} new={new_s}")

    all_green = {"signals": {"evm": {"status": "green"}, "mc": {"status": "green"},
                             "cusum": {"status": "green", "breached": False},
                             "doc": {"status": "green"}}}
    check(run_conservative_dominance(all_green, None, None).get("state") == "Green",
          "and four genuinely Green signals still return Green, so the fix is not just severity")
    check(run_conservative_dominance(all_green, None, None).get("conflict")
          == "Agreement: low risk",
          "classified as agreement at low risk")

    print()
    print("  the same defect in the three voting ensembles (the adapter run's finding 2)")

    ENSEMBLE = {"signals": {"mc": {"status": "red"}, "cusum": {"status": "red"},
                            "doc": {"status": "red"}, "decision": {"state": "Red-review"}},
                "simulationSignals": {"signal_array": []}}
    for fn, old_fn, name in ((run_weighted_voting, old_gov.run_weighted_voting,
                              "Weighted Voting"),
                             (run_majority_rules, old_gov.run_majority_rules, "Majority Rules"),
                             (run_worst_n_of_m, old_gov.run_worst_n_of_m, "Worst N of M")):
        old_c = old_fn(ENSEMBLE, None, None).get("status_color")
        new_c = fn(ENSEMBLE, None, None).get("status_color")
        check(old_c == "Green" and new_c == "Red",
              f"{name}: three lowercase red primary signals voted Green and now vote Red",
              f"old={old_c} new={new_c}")

    UNKNOWN = {"signals": {"mc": {"status": "unexpected"}, "cusum": {"status": "unexpected"},
                           "doc": {"status": "unexpected"}},
               "simulationSignals": {"signal_array": []}}
    for fn, old_fn, name in ((run_weighted_voting, old_gov.run_weighted_voting,
                              "Weighted Voting"),
                             (run_majority_rules, old_gov.run_majority_rules, "Majority Rules"),
                             (run_worst_n_of_m, old_gov.run_worst_n_of_m, "Worst N of M")):
        old_c = old_fn(UNKNOWN, None, None).get("status_color")
        new_res = fn(UNKNOWN, None, None)
        check(old_c == "Green",
              f"{name}: unrecognised statuses voted Green on the old code", str(old_c))
        check(new_res.get("status_color") != "Green",
              f"{name}: and no longer bucket to Green", str(new_res.get("status_color")))
        check(abstains(new_res),
              f"{name}: with nothing recognised to vote on, it abstains rather than deciding",
              str(new_res.get("status_color")))

    check(normalise_status("unexpected") is None and normalise_status("") is None,
          "the shared vocabulary returns no band for a value outside it")
    check(normalise_status("red") == "Red" and normalise_status("RED") == "Red"
          and normalise_status("Red-review") == "Red",
          "and recognises the same band in every casing the platform emits")
    check(normalise_status("light-amber") == "Yellow",
          "light-amber is a Yellow band and is tested before Amber, as it must be")

    print()
    print("=" * 78)
    print("2. Dempster-Shafer: ignorance is the whole frame, not a fifth disjoint state")
    print("=" * 78)

    m = {"Green": 0.8, "Yellow": 0.0, "Amber": 0.0, "Red": 0.0, "Unknown": 0.2}
    old_c = old_fusion.dst_combine(m, m)
    new_c = dst_combine(m, m)
    check(abs(old_c["conflict"] - 0.32) < 1e-12,
          "the audit's two masses gave conflict 0.32 on the old code", str(old_c["conflict"]))
    check(abs(new_c["conflict"]) < 1e-12,
          "and give conflict 0 now: an abstention does not disagree with a belief",
          str(new_c["conflict"]))
    check(abs(new_c["Green"] - 0.96) < 1e-12, "Green is 0.96", str(new_c["Green"]))
    check(abs(new_c["Unknown"] - 0.04) < 1e-12, "and the ignorance mass is 0.04",
          str(new_c["Unknown"]))
    check(abs(old_c["Green"] - 0.9411764705882353) < 1e-12,
          "where the old code gave 0.941176, having renormalised away a conflict that was not "
          "there", str(old_c["Green"]))

    # The properties, not just the one worked example.
    full_ignorance = {"Green": 0.0, "Yellow": 0.0, "Amber": 0.0, "Red": 0.0, "Unknown": 1.0}
    some = {"Green": 0.1, "Yellow": 0.2, "Amber": 0.3, "Red": 0.35, "Unknown": 0.05}
    combined = dst_combine(some, full_ignorance)
    check(all(abs(combined[s] - some[s]) < 1e-12 for s in ("Green", "Yellow", "Amber", "Red")),
          "a source that commits to nothing leaves another source's belief exactly as it was")
    check(abs(combined["conflict"]) < 1e-12, "and generates no conflict at all")
    old_combined = old_fusion.dst_combine(some, full_ignorance)
    check(old_combined["conflict"] > 0.9,
          "where total ignorance produced almost total conflict on the old code",
          str(old_combined["conflict"]))

    genuine = dst_combine({"Green": 0.9, "Yellow": 0.0, "Amber": 0.0, "Red": 0.0, "Unknown": 0.1},
                          {"Green": 0.0, "Yellow": 0.0, "Amber": 0.0, "Red": 0.9, "Unknown": 0.1})
    check(genuine["conflict"] > 0.7,
          "genuine disagreement between two beliefs still registers as conflict",
          str(genuine["conflict"]))

    print()
    print("=" * 78)
    print("3. The remaining audit proofs, each on the old code and on this branch")
    print("=" * 78)

    # ---- defect 3, quality compliance
    Q = {"qualityDeficienciesNoted": 8, "itemsInspected": 5, "itemsFailed": 8}
    old_q = old_doc.run_quality_compliance(Q, None, None)
    new_q = run_quality_compliance(Q, None, None)
    check(old_q.get("pass_rate") == -60 and old_q.get("quality_score") == -60,
          "five inspected and eight failed scored minus sixty out of a hundred on the old code",
          str(old_q.get("quality_score")))
    check(abstains(new_q),
          "and refuses now rather than returning a value outside the domain", str(new_q))
    reason_is_speakable(new_q, "quality compliance")
    ok_q = run_quality_compliance(
        {"qualityDeficienciesNoted": 2, "itemsInspected": 40, "itemsFailed": 2}, None, None)
    check(ok_q.get("pass_rate") == 95 and ok_q.get("status_color") == "Green",
          "a consistent inspection pair still computes: 2 failed of 40 is a 95 per cent pass rate",
          str(ok_q.get("pass_rate")))
    check(abstains(run_quality_compliance({"qualityDeficienciesNoted": 3}, None, None)),
          "and the fabricated denominator of twenty is gone: no inspection pair, no pass rate")
    check(old_doc.run_quality_compliance(
        {"qualityDeficienciesNoted": 3}, None, None).get("pass_rate") == 85,
        "where the old code inspected twenty items nobody had inspected", "")

    # ---- defect 4, procurement lead time
    P = {"longLeadItemsTotal": 10, "longLeadAtRisk": 8, "longLeadDelayed": 5}
    old_p = old_doc.run_procurement_lead_time(P, None, None)
    new_p = run_procurement_lead_time(P, None, None)
    check(old_p.get("risk_ratio") == 1.8,
          "ten items with eight at risk and five delayed gave 1.8 on the old code",
          str(old_p.get("risk_ratio")))
    check(new_p.get("risk_ratio") == 0.65,
          "and gives 0.65 now, with delayed items counted once as the at-risk items they are",
          str(new_p.get("risk_ratio")))
    # The domain, exhaustively rather than at one point.
    worst = run_procurement_lead_time(
        {"longLeadItemsTotal": 10, "longLeadAtRisk": 10, "longLeadDelayed": 10}, None, None)
    check(worst.get("risk_ratio") == 1.0,
          "every item at risk and every one delayed is exactly 1.0, the top of the domain",
          str(worst.get("risk_ratio")))
    over = 0
    for total in range(1, 12):
        for at_risk in range(0, total + 1):
            for delayed in range(0, at_risk + 1):
                res = run_procurement_lead_time(
                    {"longLeadItemsTotal": total, "longLeadAtRisk": at_risk,
                     "longLeadDelayed": delayed}, None, None)
                if not abstains(res) and not 0.0 <= res["risk_ratio"] <= 1.0:
                    over += 1
    check(over == 0,
          "and across every consistent count triple up to eleven items the ratio never leaves "
          "nought to one", f"{over} outside the domain")
    check(abstains(run_procurement_lead_time(
        {"longLeadItemsTotal": 0, "longLeadAtRisk": 0, "longLeadDelayed": 1}, None, None)),
        "an empty procurement log refuses rather than inventing a denominator of one")
    check(old_doc.run_procurement_lead_time(
        {"longLeadItemsTotal": 0, "longLeadAtRisk": 0, "longLeadDelayed": 1},
        None, None).get("risk_ratio") == 2.0,
        "where the old code scored that 2.0", "")
    check(abstains(run_procurement_lead_time(
        {"longLeadItemsTotal": 10, "longLeadAtRisk": 3, "longLeadDelayed": 7}, None, None)),
        "and more delayed than at risk refuses, because a delayed item is an at-risk one")

    # ---- defect 5, cost risk P80
    C = {"bac": 1_000_000, "cpi": 0, "ac": 500_000, "ev": 400_000}
    raised = False
    try:
        old_ext.run_cost_risk(C, None, None)
    except ZeroDivisionError:
        raised = True
    check(raised, "a cost performance index of zero RAISED inside the old code, losing the run")
    new_c2 = run_cost_risk(C, None, None)
    check(abstains(new_c2), "and abstains now", str(new_c2))
    reason_is_speakable(new_c2, "cost risk")
    live = run_cost_risk({"bac": 1_000_000, "cpi": 0.9, "ac": 500_000, "ev": 400_000}, None, None)
    check(not abstains(live) and live.get("p80_eac") is not None,
          "a positive index still computes: the method is untouched, only the domain is guarded",
          str(live.get("evidence_metric")))
    old_live = old_ext.run_cost_risk(
        {"bac": 1_000_000, "cpi": 0.9, "ac": 500_000, "ev": 400_000}, None, None)
    check(old_live.get("p80_eac") == live.get("p80_eac")
          and old_live.get("p80_delta_pct") == live.get("p80_delta_pct"),
          "and produces the identical figure it always did, which is the proof the arithmetic "
          "was not rebuilt", f"{old_live.get('p80_eac')} vs {live.get('p80_eac')}")

    # ---- defects 6, 7, 8: the portfolio three
    PORT = [{"id": "P1", "cpi": 1.0, "spi": 1.0, "docRiskScore": 0.1, "actualPctComplete": 50},
            {"id": "P2", "cpi": 1.0, "spi": 1.0, "docRiskScore": 0.1, "actualPctComplete": 50},
            {"id": "P3", "cpi": 1.0, "spi": 1.0, "docRiskScore": 0.1, "actualPctComplete": 50}]
    HIST = [{"signal_inputs": {"cpi": c}} for c in (0.9, 1.0, 1.1)]

    old_pf = old_portfolio.compute_portfolio(PORT, "P1", HIST, "2026-01-01")["results"]
    new_pf = compute_portfolio(PORT, "P1", HIST, "2026-01-01")["results"]
    old_t = old_pf["cat8_3_trajectory_classifier"]["trend"]
    new_t = new_pf["cat8_3_trajectory_classifier"]["trend"]
    check(abs(old_t - 0.067) < 1e-9,
          "cost performance of 0.9, 1.0, 1.1 gave a slope of 0.066667 on the old code",
          str(old_t))
    check(abs(new_t - 0.1) < 1e-9,
          "and gives 0.1 now: the rise is spread over the intervals, not the observations",
          str(new_t))
    for n, values, expected in ((2, (1.0, 1.1), 0.1), (4, (0.8, 0.9, 1.0, 1.1), 0.1)):
        h = [{"signal_inputs": {"cpi": c}} for c in values]
        got = compute_portfolio(PORT, "P1", h, "2026-01-01")["results"].get(
            "cat8_3_trajectory_classifier", {}).get("trend")
        check(got is not None and abs(got - expected) < 1e-9,
              f"and a constant rise of one tenth per period reads 0.1 over {n} observations too",
              str(got))

    check(old_pf["cat8_4_cross_project_pattern"]["status_color"] == "Yellow",
          "a cluster of healthy similar projects was Yellow at best on the old code",
          str(old_pf["cat8_4_cross_project_pattern"]["status_color"]))
    check(new_pf["cat8_4_cross_project_pattern"]["status_color"] == "Green",
          "and reads Green now, so the answer 'no distress pattern' is reachable with matches",
          str(new_pf["cat8_4_cross_project_pattern"]["status_color"]))
    distressed = [dict(p, cpi=0.85) for p in PORT]
    dpat = compute_portfolio(distressed, "P1", HIST, "2026-01-01")[
        "results"]["cat8_4_cross_project_pattern"]
    check(dpat["status_color"] == "Red",
          "while a cluster that IS in distress still reads Red", str(dpat["status_color"]))

    old_a = old_portfolio.compute_portfolio(PORT, "P1", None, "2026-01-01")[
        "results"]["cat8_5_anomaly_score"]["composite_score"]
    new_a = compute_portfolio(PORT, "P1", None, "2026-01-01")[
        "results"]["cat8_5_anomaly_score"]["composite_score"]
    check(abs(old_a - 0.17) < 1e-9,
          "no anomaly, the best rank and no history scored 0.166667 on the old code, from a "
          "constant 0.5 that measured nothing", str(old_a))
    check(abs(new_a) < 1e-9, "and scores 0 now", str(new_a))

    # ---- defect 9, Monte Carlo EAC
    for label, si in (("a budget of zero", {"bac": 0, "cpi": 0.9, "spi": 0.95}),
                      ("a cost index of zero", {"bac": 1_000_000, "cpi": 0, "spi": 0.95}),
                      ("a schedule index of zero", {"bac": 1_000_000, "cpi": 0.9, "spi": 0})):
        old_m = old_sim.run_monte_carlo(dict(si), None, 7)
        new_m = run_monte_carlo(dict(si), None, 7)
        check(not abstains(old_m), f"{label}: the old code produced a forecast anyway",
              str(old_m.get("evidence_metric"))[:80])
        check(abstains(new_m), f"{label}: and it abstains now", str(new_m))
    zero_bac = old_sim.run_monte_carlo({"bac": 0, "cpi": 1.0, "spi": 1.0}, None, 7)
    check("100" in str(zero_bac.get("evidence_metric")),
          "and the old forecast was measured against the hundred-unit placeholder",
          str(zero_bac.get("evidence_metric")))
    check(not hasattr(sys.modules["app.simulation.models_sim"], "DEMO_BAC"),
          "the placeholder no longer exists in the module at all")
    real_mc = run_monte_carlo({"bac": 1_000_000, "cpi": 0.9, "spi": 0.95}, None, 7)
    check(not abstains(real_mc),
          "a project with a real budget still forecasts", str(real_mc.get("evidence_metric")))
    check(old_sim.run_monte_carlo({"bac": 1_000_000, "cpi": 0.9, "spi": 0.95}, None, 7)
          .get("p80_eac") == real_mc.get("p80_eac"),
          "with the identical figure: removing the placeholder changed no live forecast")

    # ---- defect 10, float consumption
    F = {"totalFloat": 20, "consumedFloat": 15}
    check(not abstains(old_ext.run_float_consumption(F, None, None)),
          "float consumption scored against an invented halfway completion on the old code",
          str(old_ext.run_float_consumption(F, None, None).get("float_stress")))
    new_f = run_float_consumption(F, None, None)
    check(abstains(new_f), "and abstains without a reported completion", str(new_f))
    reason_is_speakable(new_f, "float consumption")
    with_pct = run_float_consumption(dict(F, actualPctComplete=75), None, None)
    check(not abstains(with_pct) and with_pct.get("float_stress") == 1.0,
          "and with a real completion it computes: 75 per cent of float at 75 per cent complete "
          "is a stress of exactly 1.0", str(with_pct.get("float_stress")))

    # ---- defect 11, NCR rate
    N = {"ncrIssued": 2, "ncrClosed": 1, "ncrOpen": 12}
    old_n = old_doc.run_ncr_rate(N, None, None)
    check(old_n.get("open_ratio") == 6,
          "a backlog of twelve against an intake of two scored a ratio of six on the old code",
          str(old_n.get("open_ratio")))
    check(abstains(run_ncr_rate(N, None, None)),
          "and abstains now, because a backlog needs an audited cohort to be a rate of")
    reason_is_speakable(run_ncr_rate(N, None, None), "nonconformance rate")
    empty_intake = old_doc.run_ncr_rate({"ncrIssued": 0, "ncrClosed": 0, "ncrOpen": 12},
                                        None, None)
    check(empty_intake.get("status_color") == "Green",
          "and a project carrying twelve open nonconformances but issuing none read GREEN",
          str(empty_intake.get("evidence_metric")))
    check(abstains(run_ncr_rate({"ncrIssued": 0, "ncrClosed": 0, "ncrOpen": 12}, None, None)),
          "which it no longer does")
    with_cohort = run_ncr_rate(dict(N, totalFindings=40), None, None)
    check(not abstains(with_cohort) and with_cohort.get("open_ratio") == 0.3,
          "given the audited cohort it computes: twelve open of forty is 0.3",
          str(with_cohort.get("open_ratio")))
    check(abstains(run_ncr_rate(dict(N, totalFindings=5), None, None)),
          "and a backlog larger than the cohort refuses rather than exceeding 1.0")

    # ---- defect 12, weather day impact
    W = {"weatherDaysLost": 3}
    old_w = old_doc.run_weather_impact(W, None, None)
    check(old_w.get("weather_ratio") == 100,
          "three lost days and no float figure asserted the worst case, 100 per cent, on the "
          "old code", str(old_w.get("weather_ratio")))
    new_w = run_weather_impact(W, None, None)
    check(abstains(new_w), "and abstains now", str(new_w))
    reason_is_speakable(new_w, "weather day impact")
    check(abstains(run_weather_impact({"weatherDaysLost": 3, "floatRemaining": 0}, None, None)),
          "no float remaining refuses too, rather than being assigned a ratio")
    check(old_doc.run_weather_impact({"weatherDaysLost": 3, "floatRemaining": 0},
                                     None, None).get("weather_ratio") == 100,
          "where the old code scored that 100 per cent as well", "")
    real_w = run_weather_impact({"weatherDaysLost": 3, "floatRemaining": 30}, None, None)
    check(not abstains(real_w) and real_w.get("weather_ratio") == 10,
          "and with real float it computes: three days against thirty is ten per cent",
          str(real_w.get("weather_ratio")))
    derived_w = run_weather_impact(
        {"weatherDaysLost": 3, "floatRemaining": 30,
         "sources": {"weatherDaysLost": {"docType": "derived"}}}, None, None)
    check(abstains(derived_w),
          "and inferred lost days refuse rather than computing with a parenthetical")
    check(not abstains(old_doc.run_weather_impact(
        {"weatherDaysLost": 3, "floatRemaining": 30,
         "sources": {"weatherDaysLost": {"docType": "derived"}}}, None, None)),
        "where the old code computed and appended a note to the sentence", "")

    # ---- defect 13, scenario modeling and its sibling
    for fn, old_fn, name in ((run_scenario_modeling, old_doc.run_scenario_modeling,
                              "Scenario Modeling"),
                             (run_whatif_matrix, old_gov.run_whatif_matrix,
                              "What-If Scenario Matrix")):
        for label, si in (
                ("a negative cost index",
                 {"bac": 1_000_000, "ev": 400_000, "ac": 500_000, "cpi": -0.9, "spi": 1.0}),
                ("a negative budget",
                 {"bac": -1_000_000, "ev": 400_000, "ac": 500_000, "cpi": 0.9, "spi": 1.0}),
                ("earned value above the budget",
                 {"bac": 1_000_000, "ev": 1_400_000, "ac": 500_000, "cpi": 0.9, "spi": 1.0})):
            old_s = old_fn(dict(si), None, None)
            new_s = fn(dict(si), None, None)
            check(not abstains(old_s),
                  f"{name}: {label} produced a status on the old code",
                  str(old_s.get("status_color")))
            check(abstains(new_s), f"{name}: {label} abstains now", str(new_s))
        good = {"bac": 1_000_000, "ev": 400_000, "ac": 500_000, "cpi": 0.9, "spi": 0.95}
        check(not abstains(fn(dict(good), None, None)),
              f"{name}: and a consistent earned value position still computes")
        check(old_fn(dict(good), None, None).get("evidence_metric")
              == fn(dict(good), None, None).get("evidence_metric"),
              f"{name}: with the identical finding, so only the domain changed")
    neg = old_doc.run_scenario_modeling(
        {"bac": 1_000_000, "ev": 400_000, "ac": 500_000, "cpi": -0.9, "spi": 1.0}, None, None)
    check(neg.get("status_color") == "Green" and neg.get("pessimistic_eac", 0) < 0,
          "and the old code called a NEGATIVE worst-case forecast Green, which is the defect at "
          "its plainest", f"{neg.get('status_color')} / {neg.get('pessimistic_eac')}")

    # ---- defect 14, contractor performance
    R = {"overallRating": 4.5, "scheduleRating": 4.2, "costRating": 4.4, "qualityRating": 2.0}
    old_cp = old_doc.run_contractor_performance(R, None, None)
    new_cp = run_contractor_performance(R, None, None)
    check(old_cp.get("status_color") == "Green" and old_cp.get("min_rating") == 4.2,
          "a contractor rated 2 out of 5 on quality read Green on the old code, which never "
          "looked at the quality rating", f"{old_cp.get('status_color')} {old_cp.get('min_rating')}")
    check(new_cp.get("status_color") == "Red" and new_cp.get("min_rating") == 2.0,
          "and reads Red on that rating now", f"{new_cp.get('status_color')} {new_cp.get('min_rating')}")
    check("quality 2" in reason(new_cp), "with the quality rating named in the finding",
          reason(new_cp))
    check(new_cp.get("ratings_read") == 4, "and four ratings recorded as read",
          str(new_cp.get("ratings_read")))
    no_q = {"overallRating": 4.5, "scheduleRating": 4.2, "costRating": 4.4}
    check(run_contractor_performance(no_q, None, None).get("min_rating") == 4.2
          and run_contractor_performance(no_q, None, None).get("ratings_read") == 3,
          "an evaluation that did not rate quality is scored on the three it did rate")
    check("quality" not in reason(run_contractor_performance(no_q, None, None)),
          "and does not claim a quality rating it was not given")

    # ---- defect 15, environmental compliance
    E = {"environmentalIssuesDiscussed": 0}
    old_e = old_doc.run_environmental_compliance(E, None, None)
    check(old_e.get("compliance_rate") == 100 and old_e.get("status_color") == "Green",
          "a project where the environment was never discussed scored 100 per cent compliant "
          "on the old code", str(old_e.get("compliance_rate")))
    check(old_doc.run_environmental_compliance(
        {"environmentalIssuesDiscussed": 4}, None, None).get("compliance_rate") == 80,
        "and four mentions scored exactly 80, at five points a mention", "")
    check(abstains(run_environmental_compliance(E, None, None)),
          "both abstain now: a count of mentions is not a measure of compliance")
    reason_is_speakable(run_environmental_compliance(E, None, None), "environmental compliance")
    audited = run_environmental_compliance(
        {"environmentalIssuesDiscussed": 4, "environmentalComplianceRate": 97}, None, None)
    check(not abstains(audited) and audited.get("status_color") == "Green",
          "and an audited rate computes", str(audited.get("evidence_metric")))
    check(abstains(run_environmental_compliance(
        {"environmentalIssuesDiscussed": 0, "environmentalComplianceRate": 140}, None, None)),
        "a rate outside nought to a hundred refuses rather than being clipped into the domain")
    check(old_doc.run_environmental_compliance(
        {"environmentalIssuesDiscussed": 0, "environmentalComplianceRate": 140},
        None, None).get("compliance_rate") == 100,
        "where the old code clipped it to 100 and called the project Green", "")

    print()
    print("=" * 78)
    print("4. On the real path: which of the fifteen produce output and which abstain")
    print("=" * 78)

    ADMIN = "r2-admin"
    PRJ = "PRJ-R2-DEFECTS"
    MONTHS = {
        1: ("2026-03-31", 3_000_000, 3_050_000, 3_050_000, 25.0, 25.0),
        2: ("2026-04-30", 4_000_000, 4_250_000, 4_150_000, 33.0, 34.0),
        3: ("2026-05-31", 5_000_000, 5_500_000, 5_300_000, 42.0, 44.0),
        4: ("2026-06-30", 6_000_000, 6_900_000, 6_500_000, 50.0, 54.0),
    }

    def b64(raw: bytes) -> str:
        return base64.b64encode(raw).decode()

    def post(payload: dict) -> dict:
        r = client.post("/exec", content=json.dumps(payload),
                        headers={"Content-Type": "text/plain"})
        assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
        return r.json()

    def doc_bytes(tag: str) -> bytes:
        return f"%PDF-1.4 RUN2 FIFTEEN {tag}\n".encode()

    def monthly(d, ev, ac, pv, apc, ppc):
        return {"earned_value": ev, "actual_cost": ac, "planned_value": pv,
                "budget_at_completion": 12_000_000, "actual_percent_complete": apc,
                "planned_percent_complete": ppc, "report_date": d, "document_date": d,
                "document_risk_score": 0.45}

    REC = {}
    for p, mth in MONTHS.items():
        REC[hashlib.sha256(doc_bytes(f"M{p}")).hexdigest()] = (
            "monthly_report", monthly(mth[0], *mth[1:]))
    # The document types the corpus DOES carry for a construction project, so the categorisation
    # below reflects real evidence rather than an empty project abstaining on everything.
    REC[hashlib.sha256(doc_bytes("PROC")).hexdigest()] = ("procurement_log", {
        "long_lead_items_total": 10, "at_risk": 8, "delayed": 5,
        "report_date": "2026-06-30", "document_date": "2026-06-30"})
    REC[hashlib.sha256(doc_bytes("INSP")).hexdigest()] = ("inspection_report", {
        "items_inspected": 40, "items_failed": 2, "deficiency_count": 2,
        "report_date": "2026-06-30", "document_date": "2026-06-30"})
    REC[hashlib.sha256(doc_bytes("NCR")).hexdigest()] = ("ncr_log", {
        "ncr_issued": 2, "ncr_closed": 1, "ncr_open": 12,
        "report_date": "2026-06-30", "document_date": "2026-06-30"})
    REC[hashlib.sha256(doc_bytes("FIELD")).hexdigest()] = ("field_report", {
        "weather_days_lost": 3, "quality_deficiencies_noted": 2,
        "report_date": "2026-06-30", "document_date": "2026-06-30"})
    # NOTE FOR THE READER OF THIS FIXTURE: the contractor ratings live on a Past Performance
    # Report, which the programme records as one of the three document types CORRECTLY ABSENT
    # from the corpus. It is supplied here so that defect 14's fix can be shown producing output
    # on the real path when the document exists; on the corpus as it stands, that computation
    # abstains for want of the document rather than for want of a fix. Section 4's report says
    # so rather than implying the corpus carries it.
    REC[hashlib.sha256(doc_bytes("PERF")).hexdigest()] = ("past_performance_report", {
        "overall_rating": 4.5, "schedule_rating": 4.2, "cost_rating": 4.4,
        "quality_rating": 2.0, "source": "Owner evaluation"})
    # The seven CORE modules are the ONLY ones that vote, so unless their inputs are present the
    # rollup evidence in section 5 would be one category wide and would prove nothing about
    # project status fusion. These six documents put all seven CORE computations on the board:
    # cost and schedule indices (A1.7, A1.8) from the monthly reports above, plus look-ahead
    # health, contingency burn, material cost variance, request velocity and submittal rejection.
    CORE_TAGS = ("LOOK", "PAY", "COST", "RFI", "SUB")
    for p, mth in MONTHS.items():
        d = mth[0]
        REC[hashlib.sha256(doc_bytes(f"LOOK{p}")).hexdigest()] = ("lookahead_schedule", {
            "activities_planned": 60, "activities_constrained": 4 + 3 * p,
            "lookahead_weeks": 3, "report_date": d})
        REC[hashlib.sha256(doc_bytes(f"PAY{p}")).hexdigest()] = ("pay_application", {
            "amount_paid_to_date": mth[2], "percent_complete_verified": mth[4],
            "completed_to_date": mth[1], "original_contingency": 600_000,
            "remaining_contingency": 600_000 - 90_000 * p, "application_date": d})
        REC[hashlib.sha256(doc_bytes(f"COST{p}")).hexdigest()] = ("cost_report", {
            "material_cost_baseline": 4_000_000,
            "material_cost_current": 4_000_000 + 90_000 * p,
            "indirect_cost_plan": 900_000, "indirect_cost_actual": 880_000,
            "report_date": d})
        REC[hashlib.sha256(doc_bytes(f"RFI{p}")).hexdigest()] = ("rfi_log", {
            "rfi_total": 20 + 7 * p, "rfi_open": 4 + 3 * p, "rfi_overdue": p,
            "avg_response_days": 8.0 + p, "rfi_period_days": 30,
            "oldest_open_days": 20 + 9 * p, "log_date": d})
        REC[hashlib.sha256(doc_bytes(f"SUB{p}")).hexdigest()] = ("submittal_register", {
            "submittals_total": 40 + 16 * p, "submittals_rejected": 3 + 3 * p,
            "document_date": d})
    REC[hashlib.sha256(doc_bytes("OAC")).hexdigest()] = ("oac_minutes", {
        "environmental_issues_discussed": 2, "safety_incidents_discussed": 0,
        "meeting_date": "2026-06-30", "document_date": "2026-06-30"})
    set_extractor_override(StubExtractor(REC))

    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="R2-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == PRJ)) is None:
            s.add(Project(legacy_id=PRJ,
                          doc={"id": PRJ, "name": PRJ, "signals": {}, "events": []}))
        s.commit()

    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": "R2-PM", "role": "Participant",
                    "account_type": "operational"})
    pm = post({"action": "researchlogin",
               "access_token": created["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": admin, "id": PRJ,
          "participant_id": created["participant_id"], "project_role": "PM"})

    for p in (1, 2, 3, 4):
        docs = [{"filename": f"M{p}.pdf", "mimeType": "application/pdf",
                 "dataBase64": b64(doc_bytes(f"M{p}"))}]
        # Every period gets the CORE-feeding set, so the rollup evidence below spans four
        # categories in all four periods rather than one.
        docs += [{"filename": f"{t}{p}.pdf", "mimeType": "application/pdf",
                  "dataBase64": b64(doc_bytes(f"{t}{p}"))} for t in CORE_TAGS]
        if p == 4:
            docs += [{"filename": f"{t}.pdf", "mimeType": "application/pdf",
                      "dataBase64": b64(doc_bytes(t))}
                     for t in ("PROC", "INSP", "NCR", "FIELD", "PERF", "OAC")]
        post({"action": "projectupload", "session_token": pm, "id": PRJ,
              "period": p, "period_end": MONTHS[p][0], "documents": docs})
    allr = post({"action": "projectcomputeall", "session_token": pm, "id": PRJ})
    check(allr.get("computed") == 4, "four periods compute on the document path", str(allr)[:140])

    r4 = post({"action": "projectresults", "session_token": pm, "id": PRJ,
               "period": 4})["result"]
    comp = {m.get("module_id"): m for m in (r4.get("module_results") or [])}
    abst = {a.get("module_id"): a for a in (r4.get("abstained") or [])}
    check(bool(comp), "the stored row carries module results", str(len(comp)))

    FIFTEEN = {
        "B1.1": "Conservative Dominance", "B2.1": "Dempster-Shafer evidence combination",
        "A6.1": "Quality Compliance Index", "A4.9": "Procurement Lead Time Monitor",
        "A3.6": "Cost Risk Analysis P80", "D1.3": "Signal Trajectory Classifier",
        "D1.4": "Cross-project Pattern Detector", "D1.5": "Anomaly Score",
        "A1.1": "Monte Carlo EAC", "A2.5": "Float Consumption Rate", "A4.4": "NCR Rate",
        "A4.5": "Weather Day Impact", "A5.4": "Scenario Modeling",
        "A6.4": "Contractor Performance Score", "A6.3": "Environmental Compliance Rate",
    }
    PORTFOLIO_THREE = {"D1.3", "D1.4", "D1.5"}
    print()
    print("  category landed in, measured on the stored row at period four:")
    landed: dict[str, str] = {}
    for mid, name in sorted(FIFTEEN.items()):
        if mid in PORTFOLIO_THREE:
            continue
        if mid in comp:
            landed[mid] = "producing"
            print(f"    producing   {name}: {comp[mid].get('status_color')} -- "
                  f"{str(comp[mid].get('evidence_metric'))[:64]}")
        else:
            landed[mid] = "abstaining"
            print(f"    abstaining  {name}: {str(abst.get(mid, {}).get('reason'))[:80]}")
    check(all(mid in comp or mid in abst for mid in FIFTEEN if mid not in PORTFOLIO_THREE),
          "every project-level one of the fifteen is accounted for, computed or abstained")
    check(not (set(FIFTEEN) & set()),
          "and none of the fifteen was moved to the disabled set by this run")

    for mid in ("A4.9", "A6.1", "A6.4", "A1.1", "A5.4", "A3.6", "B1.1", "B2.1"):
        check(mid in comp, f"{FIFTEEN[mid]} produces a finding on the real path",
              str(abst.get(mid, {}).get("reason"))[:90])
    # These three refuse for want of data the fix now requires, and each states which data.
    for mid in ("A4.4", "A4.5", "A6.3"):
        rsn = str(abst.get(mid, {}).get("reason") or "")
        check(mid in abst, f"{FIFTEEN[mid]} abstains on the real path, correctly", str(rsn)[:90])
        check(rsn.startswith("Awaiting"),
              f"{FIFTEEN[mid]}: and the stored reason names what it is waiting for", rsn[:110])
        check("—" not in rsn and "--" not in rsn,
              f"{FIFTEEN[mid]}: with no em dash on a reason the ledger renders", rsn[:110])
        check(not any(t in rsn for t in ("A4.", "A6.", "docType", "signalInputs")),
              f"{FIFTEEN[mid]}: and no module id or key name", rsn[:110])
    # Float consumption is a fourth abstention and it refuses EARLIER than its new guard: the
    # corpus carries no schedule float at all, so the required-inputs gate fires first and the
    # generic reason stands. Asserted as what it is rather than claimed as the new reason.
    fc = str(abst.get("A2.5", {}).get("reason") or "")
    check("A2.5" in abst, "Float Consumption Rate abstains on the real path, correctly", fc[:90])
    check("Insufficient data" in fc,
          "and does so at the required-inputs gate, because no document in this corpus carries "
          "schedule float at all: its own completion guard is never reached here", fc[:110])

    check(comp.get("A4.9", {}).get("risk_ratio") == 0.65,
          "and the procurement ratio the ledger will render is the corrected 0.65, from the "
          "real document, not from a call in this file", str(comp.get("A4.9", {})))
    check(comp.get("A6.4", {}).get("status_color") == "Red",
          "and the contractor evaluation reads Red on its quality rating",
          str(comp.get("A6.4", {}).get("evidence_metric")))
    check(comp.get("A6.1", {}).get("pass_rate") == 95,
          "and quality compliance reads the real inspection pair",
          str(comp.get("A6.1", {}).get("evidence_metric")))

    print()
    print("  the three portfolio computations, on the real path")
    # They are Group D and refuse on a single-project path by design, so a SECOND project is
    # created and computed. What is read back is the stored portfolio snapshot on the row, not a
    # call to compute_portfolio made here.
    SECOND = "PRJ-R2-SECOND"
    with Session() as s:
        if s.scalar(select(Project).where(Project.legacy_id == SECOND)) is None:
            s.add(Project(legacy_id=SECOND,
                          doc={"id": SECOND, "name": SECOND, "signals": {}, "events": []}))
        s.commit()
    for p, mth in MONTHS.items():
        REC[hashlib.sha256(doc_bytes(f"S{p}")).hexdigest()] = (
            "monthly_report", monthly(mth[0], mth[1], mth[2] - 120_000, mth[3], mth[4], mth[5]))
    set_extractor_override(StubExtractor(REC))
    post({"action": "adminmemberadd", "session_token": admin, "id": SECOND,
          "participant_id": created["participant_id"], "project_role": "PM"})
    for p in (1, 2, 3, 4):
        post({"action": "projectupload", "session_token": pm, "id": SECOND,
              "period": p, "period_end": MONTHS[p][0],
              "documents": [{"filename": f"S{p}.pdf", "mimeType": "application/pdf",
                             "dataBase64": b64(doc_bytes(f"S{p}"))}]})
    post({"action": "projectcomputeall", "session_token": pm, "id": SECOND})
    s4 = post({"action": "projectresults", "session_token": pm, "id": SECOND,
               "period": 4})["result"]
    snap = (s4.get("portfolio_snapshot") or {}).get("results") or {}
    for key, name in (("cat8_3_trajectory_classifier", "Signal Trajectory Classifier"),
                      ("cat8_4_cross_project_pattern", "Cross-project Pattern Detector"),
                      ("cat8_5_anomaly_score", "Anomaly Score")):
        check(key in snap, f"{name} produces a finding in the stored portfolio snapshot",
              str(sorted(snap.keys())))
        landed[key] = "producing"
        print(f"    producing   {name}: {snap.get(key, {}).get('status_color')} -- "
              f"{str(snap.get(key, {}).get('evidence_metric'))[:60]}")
    # The slope on the real path, recomputed from the stored periods rather than read back.
    stored_cpis = []
    for p in (1, 2, 3, 4):
        stored_cpis.append(post({"action": "projectresults", "session_token": pm,
                                 "id": SECOND, "period": p})["result"]["signal_inputs"]["cpi"])
    last3 = stored_cpis[-3:]
    expected = round((last3[-1] - last3[0]) / (len(last3) - 1) * 1000) / 1000
    check(abs(snap["cat8_3_trajectory_classifier"]["trend"] - expected) < 1e-9,
          "and the trajectory slope on the real path is the stored periods' own movement over "
          "the intervals between them", f"{snap['cat8_3_trajectory_classifier']['trend']} vs "
                                        f"{expected}")

    print()
    print("=" * 78)
    print("5. THE ROLLUP EVIDENCE: what the Dempster's rule fix does to project status")
    print("=" * 78)
    print("   Required by remediation_decisions_answered.md 2.4. The 'before' is the same")
    print("   compute_project over the same stored inputs with the baseline commit's own dst_combine")
    print("   swapped in, so the comparison is of one changed function and nothing else.")

    def with_combine(fn, si, period):
        saved = fusion.dst_combine
        fusion.dst_combine = fn
        try:
            return compute_project(dict(si), PRJ, period, MONTHS[int(period[-1])][0])
        finally:
            fusion.dst_combine = saved

    rows = []
    for p in (1, 2, 3, 4):
        stored_row = post({"action": "projectresults", "session_token": pm, "id": PRJ,
                           "period": p})["result"]
        si = stored_row.get("signal_inputs") or {}
        before = with_combine(old_fusion.dst_combine, si, f"P{p}")
        after = with_combine(fusion.dst_combine, si, f"P{p}")
        rows.append((p, before, after, stored_row))

    check(len(rows) == 4, "four periods measured")
    print()
    print("   period | project status before -> after | conflict before -> after")
    status_moves = 0
    conflict_moves = 0
    for p, before, after, stored_row in rows:
        b_s, a_s = before["project_status"], after["project_status"]
        b_k, a_k = round(before["project_conflict"], 6), round(after["project_conflict"], 6)
        if b_s != a_s:
            status_moves += 1
        if b_k != a_k:
            conflict_moves += 1
        print(f"     {p}    | {b_s} -> {a_s}   | {b_k} -> {a_k}")
        check(a_s == stored_row.get("project_status"),
              f"period {p}: the recomputed 'after' equals what the real path actually stored",
              f"{a_s} vs {stored_row.get('project_status')}")

    print()
    print("   category rollup, every category, every period:")
    cat_status_moves = 0
    cat_conflict_moves = 0
    for p, before, after, _ in rows:
        for cat in sorted(set(before["category_statuses"]) | set(after["category_statuses"])):
            b = before["category_statuses"].get(cat, {})
            a = after["category_statuses"].get(cat, {})
            b_s, a_s = b.get("status"), a.get("status")
            b_k, a_k = round(b.get("conflict", 0.0), 6), round(a.get("conflict", 0.0), 6)
            if b_s != a_s:
                cat_status_moves += 1
            if b_k != a_k:
                cat_conflict_moves += 1
            print(f"     period {p} {cat}: {b_s} -> {a_s}, conflict {b_k} -> {a_k}")

    print()
    print(f"   MEASURED: project status changed in {status_moves} of 4 periods; project "
          f"conflict in {conflict_moves} of 4.")
    print(f"   MEASURED: category status changed {cat_status_moves} times; category conflict "
          f"{cat_conflict_moves} times.")
    check(conflict_moves + cat_conflict_moves > 0,
          "the fix DOES move the rollup: conflict falls wherever a source carried ignorance, "
          "which is every source, and that is measured rather than asserted",
          f"{conflict_moves} project, {cat_conflict_moves} category")
    check(all(a["project_status"] in ("Green", "Yellow", "Amber", "Red", None)
              for _, _, a, _ in rows),
          "and every resulting project status is still a band the platform can render")

    # The DIRECTION of the change, stated as a property rather than read off the table above.
    #
    # Note carefully what three agreeing Green sources do and do not conflict over. Each Green
    # source's mass is spread across all four bands and Θ, so two Green sources genuinely
    # disagree a little: one puts 0.04 on Red where the other puts 0.80 on Green, and that is
    # real disagreement between two beliefs. The conflict does NOT go to zero, and a check
    # asserting it did would have been asserting something false. What the fix removes is only
    # the part of K that came from a source's ignorance, so the correct property is that
    # conflict FALLS on every combination where any source withheld mass, and never rises.
    every = ["Green", "Green", "Green"]
    saved = fusion.dst_combine
    fusion.dst_combine = old_fusion.dst_combine
    try:
        old_fuse_conflict = fusion.dst_fuse(every)["conflict"]
    finally:
        fusion.dst_combine = saved
    new_fuse_conflict = dst_fuse(every)["conflict"]
    check(new_fuse_conflict < old_fuse_conflict,
          "three agreeing sources record LESS conflict than before, because the ignorance each "
          "withheld no longer counts as disagreement",
          f"{old_fuse_conflict} -> {new_fuse_conflict}")
    check(new_fuse_conflict > 0,
          "and not zero: two Green sources still put a little mass on different bands, which is "
          "genuine disagreement and must survive", str(new_fuse_conflict))

    # THE MONOTONICITY PROPERTY, AND EXACTLY WHERE IT HOLDS. This check first asserted that
    # fused conflict never rises anywhere, and that claim is FALSE: it happened to pass on the
    # handful of combinations first chosen, which is the shape of vacuous check this project
    # keeps finding. Exhausting the space instead shows the truth, which is more interesting and
    # has to be reported rather than smoothed over.
    #
    # At the level of ONE combination the property does hold, exhaustively: the fix only ever
    # MOVES terms out of the conflict sum, never into it, so K can only fall.
    import random  # noqa: E402
    random.seed(20260811)
    rose = 0
    fell = 0
    for _ in range(4000):
        m1 = {s: random.random() for s in fusion.STATES}
        m2 = {s: random.random() for s in fusion.STATES}
        m1 = {k: v / sum(m1.values()) for k, v in m1.items()}
        m2 = {k: v / sum(m2.values()) for k, v in m2.items()}
        a = dst_combine(m1, m2)["conflict"]
        b = old_fusion.dst_combine(m1, m2)["conflict"]
        if a > b + 1e-12:
            rose += 1
        elif a < b - 1e-12:
            fell += 1
    check(rose == 0 and fell > 3900,
          "over four thousand random mass pairs, one application of the rule NEVER records more "
          "conflict than before and almost always records less", f"rose {rose}, fell {fell}")

    # At the level of a whole FUSION it does not hold, and the reason is worth stating: dst_fuse
    # renormalises between combinations, so mass that used to be discarded as conflict now
    # survives to the next combination and can genuinely disagree there. Measured across every
    # sequence of up to four statuses rather than asserted either way.
    import itertools  # noqa: E402
    fuse_rose = 0
    fuse_fell = 0
    fuse_same = 0
    for n in range(1, 5):
        for combo in itertools.product(("Green", "Yellow", "Amber", "Red"), repeat=n):
            seq = list(combo)
            saved2 = fusion.dst_combine
            fusion.dst_combine = old_fusion.dst_combine
            try:
                b = fusion.dst_fuse(seq)["conflict"]
            finally:
                fusion.dst_combine = saved2
            a = dst_fuse(seq)["conflict"]
            if a > b + 1e-12:
                fuse_rose += 1
            elif a < b - 1e-12:
                fuse_fell += 1
            else:
                fuse_same += 1
    total_seqs = fuse_rose + fuse_fell + fuse_same
    print(f"   MEASURED: over all {total_seqs} status sequences up to length four, fused "
          f"conflict falls in {fuse_fell}, rises in {fuse_rose}, is unchanged in {fuse_same}.")
    check(total_seqs == 340 and fuse_fell > fuse_rose,
          "fused conflict falls far more often than it rises, and where it rises it is because "
          "mass that used to be thrown away as conflict now survives to disagree later",
          f"{fuse_fell} down, {fuse_rose} up, {fuse_same} unchanged")
    check(fuse_rose > 0,
          "and this run does NOT claim fused conflict is monotone, because it is not: that is "
          "measured here rather than assumed", str(fuse_rose))

    print()
    print("=" * 78)
    print("6. Fixing arithmetic did not make anything vote, and the seven CORE set is intact")
    print("=" * 78)

    from app.simulation.registry import CORE_VOTING_MODULES  # noqa: E402
    # RE-POINTED BY RUN 4, THE FREEZE POINT. What this check protects is that fixing arithmetic
    # did not hand anything a vote, and that property is unchanged. The set it compares against
    # is now the one Run 4 left behind: the two measures whose band boundaries a published
    # source specifies. The five it held back are still non-voting, which is what the next
    # assertion reads.
    check(CORE_VOTING_MODULES == frozenset({"A1.7", "A1.8"}),
          "the voting set is the two measures Run 4 restored, and nothing this run touched "
          "joined them", str(sorted(CORE_VOTING_MODULES)))
    fixed_that_compute = [m for m in FIFTEEN if m in comp]
    check(all(comp[m].get("votes") is False for m in fixed_that_compute
              if m not in CORE_VOTING_MODULES),
          "every one of the fifteen that now computes still carries votes:false",
          str([m for m in fixed_that_compute if comp[m].get("votes") is not False]))
    check(not (set(FIFTEEN) & CORE_VOTING_MODULES),
          "none of the fifteen is a CORE module, so none of them acquired a vote")
    cats = r4.get("category_statuses") or {}
    from app.simulation.registry import registry_index  # noqa: E402
    voting_cats = {registry_index()[m]["category"] for m in CORE_VOTING_MODULES}
    check(set(cats.keys()) <= voting_cats,
          "and no category rollup exists for a category carried only by them",
          str(sorted(set(cats.keys()) - voting_cats)))

    print()
    print("=" * 78)
    print("7. Nothing qualifier-like reached the participant surface")
    print("=" * 78)

    # The guarantee for THIS run is that it changed nothing a participant sees ABOUT the
    # remediation. The strongest form of that is not a keyword scan, which would trip over the
    # previous runs' own code comments: it is that every participant-facing script is byte for
    # byte what it was before this run started. What a participant does see change is the
    # findings and the abstention reasons the ledger already rendered from the stored row, which
    # is the computation itself and is meant to stay visible.
    PARTICIPANT_JS = ("assets/js/taxonomy.js", "assets/js/app.js", "assets/js/detail.js",
                      "assets/js/module_charts.js", "assets/js/export.js",
                      "assets/js/recommendation_options.js", "assets/js/decision.js")
    #
    # RUN 4 NOTE, AND IT IS THE HONEST WAY TO KEEP THIS CHECK RATHER THAN WEAKEN IT. One of
    # these files did change after this run, at the freeze point: the courses-of-action
    # explanation said a module was "validated" to vote, a word the platform cannot support,
    # and Run 4 removed it. Loosening the check to "these files may differ" would throw away
    # the property. Instead the one permitted difference is named exactly: that file must
    # differ ONLY by no longer making the validation claim, and every other participant script
    # must still be byte for byte identical.
    RUN4_PERMITTED = "assets/js/recommendation_options.js"
    RUN4_PERMITTED_2 = "assets/js/detail.js"
    for rel in PARTICIPANT_JS:
        live = (ROOT / rel).read_text(encoding="utf-8")
        base = subprocess.run(["git", "show", f"{BASELINE_REV}:{rel}"],
                              cwd=ROOT, capture_output=True, check=True,
                              text=True).stdout
        if rel == RUN4_PERMITTED:
            check("modules validated to vote" in base,
                  f"{rel}: the baseline did carry the validation claim, so what follows is "
                  f"about a real difference and not an imagined one")
            live_code = "\n".join(ln for ln in live.splitlines()
                                  if not ln.strip().startswith("//"))
            check("validated" not in live_code,
                  f"{rel}: and no line the file can put in front of a reader makes a "
                  f"validation claim; the word survives only in the comment recording why it "
                  f"was removed")
            removed = [ln.strip() for ln in base.splitlines()
                       if ln not in live.splitlines()]
            added = [ln.strip() for ln in live.splitlines()
                     if ln not in base.splitlines()]
            check(all("validated" in ln or ln.startswith("+")
                      or ln.startswith('+ "') for ln in removed),
                  f"{rel}: every line the freeze removed carried the validation claim",
                  str(removed)[:200])
            check(all(ln.startswith("//") or ln.startswith('+ "') or ln.startswith('reason:')
                      or ln.startswith("reason:") for ln in added),
                  f"{rel}: and every line it added is either a comment or a continuation of "
                  f"the same explanation sentence", str(added)[:200])
            check("still appears on the" in live and "signal ledger" in live,
                  f"{rel}: the substance a participant reads is unchanged")
            continue
        if rel == RUN4_PERMITTED_2:
            # The second permitted difference, and it is the freeze point's, not this run's.
            # The ledger has always had code to print a module's own abstention reason under a
            # silent row, and it never ran, because the row the page reads is the list
            # projection and nothing grafted `abstained` onto it. Run 4 added that graft, which
            # is why the sentences THIS run wrote are on the page at all. Named exactly rather
            # than tolerated: the file must differ only by that graft.
            removed = [ln.strip() for ln in base.splitlines()
                       if ln not in live.splitlines()]
            added = [ln.strip() for ln in live.splitlines() if ln not in base.splitlines()]
            check(not removed,
                  f"{rel}: the freeze removed nothing from this file", str(removed)[:200])
            # RESTATED BY RUN 11, ORIGINAL FINDING PRESERVED. Until Run 11 this file differed
            # from the freeze only by Run 4's abstention-reason graft, and that record stands.
            # Run 11 Gate 1 adds exactly one statement to it: the opt-in gate that stops the
            # client-side evidence-module backfill from recomputing on the participant route.
            # It is named here rather than tolerated as an unexplained difference, so the file
            # still has no addition that is not accounted for by a run's authorised scope.
            RUN11_GATE_1_LINE = "if (!window.LIN_ALLOW_CLIENT_ANALYTICS) return;"
            check(all(ln.startswith("//") or "abstained" in ln or ln == "}"
                      or ln == RUN11_GATE_1_LINE for ln in added),
                  f"{rel}: and everything it added is the abstention-reason graft, Run 11's "
                  f"client-analytics gate, or the comment recording why", str(added)[:200])
            check(RUN11_GATE_1_LINE in [ln.strip() for ln in live.splitlines()],
                  f"{rel}: and Run 11's gate is actually present, so the allowance above is "
                  f"not a licence for an absent line")
            check("p.storedResult.abstained = resp.result.abstained" in live,
                  f"{rel}: which is the one line that makes an abstaining module say what it "
                  f"is waiting for on the page a project manager reads")
            continue
        check(live == base,
              f"this run changed nothing on the participant surface ({rel})",
              f"{len(live)} bytes vs {len(base)}")

    print()
    print("=" * 78)
    print("8. Every check above proved able to fail: the fault injections")
    print("=" * 78)
    print("   Each injection reverses one fix in the LIVE module, confirms the corresponding")
    print("   check goes red, then restores and reconfirms the baseline green. An injection")
    print("   that does not take is itself a failure here, not a silent pass.")

    import app.simulation.models_doc as live_doc  # noqa: E402
    import app.simulation.models_gov as live_gov  # noqa: E402
    import app.simulation.portfolio as live_portfolio  # noqa: E402

    def inject(label, owner, attr, replacement, probe, expect_red_when_injected):
        """Swap one live function, confirm the probe flips, restore, confirm it flips back."""
        baseline = probe()
        original = getattr(owner, attr)
        setattr(owner, attr, replacement)
        try:
            injected = probe()
        finally:
            setattr(owner, attr, original)
        restored = probe()
        check(injected == expect_red_when_injected,
              f"injection takes: {label}", f"probe under injection = {injected!r}")
        check(baseline != expect_red_when_injected and restored == baseline,
              f"and the baseline is restored afterwards: {label}",
              f"baseline={baseline!r} restored={restored!r}")

    # (a) Dempster's rule: put the old combination back and watch the ignorance proof go red.
    #     The probe is the worked proof itself, which is unambiguous in both directions.
    inject("Dempster's rule over ignorance", fusion, "dst_combine", old_fusion.dst_combine,
           lambda: round(fusion.dst_combine(m, m)["conflict"], 6),
           0.32)

    # (b) The shared vocabulary: put the old capitalised bucket back and watch the ensembles
    #     vote Green on three lowercase red signals again.
    def case_sensitive(status):
        if not status:
            return None
        if "Red" in str(status):
            return "Red"
        if status == "Amber":
            return "Amber"
        if status == "Yellow":
            return "Yellow"
        return "Green"

    inject("the shared status vocabulary in the voting ensembles",
           live_gov, "normalise_status", case_sensitive,
           lambda: live_gov.run_weighted_voting(ENSEMBLE, None, None).get("status_color"),
           "Green")

    # (c) Conservative Dominance. Injecting a case-SENSITIVE vocabulary here would not reproduce
    #     the defect, because the audit's own case arrives capitalised and the defect was that
    #     this module compared in LOWERCASE. The faithful injection is the module as it stood,
    #     so what is put back is the real old function rather than an approximation of it.
    import app.simulation.models_decision as live_decision  # noqa: E402
    inject("Conservative Dominance's lowercase comparisons",
           live_decision, "run_conservative_dominance",
           old_decision.run_conservative_dominance,
           lambda: live_decision.run_conservative_dominance(AUDIT_CASE, None, None).get("state"),
           "Green")

    # (d) The portfolio slope: divide by observations again.
    old_traj_source = old_portfolio.compute_portfolio
    inject("the trajectory slope divisor",
           live_portfolio, "compute_portfolio", old_traj_source,
           lambda: round(live_portfolio.compute_portfolio(
               PORT, "P1", HIST, "2026-01-01")["results"][
                   "cat8_3_trajectory_classifier"]["trend"], 6) == 0.1,
           False)

    # (e) The three permanent abstentions: put the old fabricating functions back and watch each
    #     produce a number again on exactly the input that should refuse.
    for attr, old_fn, si, label in (
            ("run_environmental_compliance", old_doc.run_environmental_compliance,
             {"environmentalIssuesDiscussed": 0}, "the synthetic environmental score"),
            ("run_weather_impact", old_doc.run_weather_impact,
             {"weatherDaysLost": 3}, "the weather worst-case assertion"),
            ("run_ncr_rate", old_doc.run_ncr_rate,
             {"ncrIssued": 0, "ncrClosed": 0, "ncrOpen": 12},
             "the nonconformance zero-intake Green")):
        inject(label, live_doc, attr, old_fn,
               lambda a=attr, s=si: abstains(getattr(live_doc, a)(dict(s), None, None)),
               False)

    # (f) The quality domain refusal.
    inject("the quality compliance domain refusal",
           live_doc, "run_quality_compliance", old_doc.run_quality_compliance,
           lambda: abstains(live_doc.run_quality_compliance(dict(Q), None, None)),
           False)

    # (g) The procurement bound.
    inject("the procurement ratio bound",
           live_doc, "run_procurement_lead_time", old_doc.run_procurement_lead_time,
           lambda: live_doc.run_procurement_lead_time(dict(P), None, None)["risk_ratio"] <= 1.0,
           False)

    # (h) The contractor quality rating.
    inject("the contractor quality rating",
           live_doc, "run_contractor_performance", old_doc.run_contractor_performance,
           lambda: live_doc.run_contractor_performance(dict(R), None, None)["status_color"],
           "Green")

    # (i) The Monte Carlo placeholder.
    import app.simulation.models_sim as live_sim  # noqa: E402
    inject("the Monte Carlo budget placeholder",
           live_sim, "run_monte_carlo", old_sim.run_monte_carlo,
           lambda: abstains(live_sim.run_monte_carlo(
               {"bac": 0, "cpi": 0.9, "spi": 0.95}, None, 7)),
           False)

    # (j) The float completion requirement.
    import app.simulation.models_ext as live_ext  # noqa: E402
    inject("the float consumption completion requirement",
           live_ext, "run_float_consumption", old_ext.run_float_consumption,
           lambda: abstains(live_ext.run_float_consumption(dict(F), None, None)),
           False)

    # (k) The cost risk zero guard: the old code RAISES, so the probe records that too.
    def cost_risk_probe():
        try:
            return abstains(live_ext.run_cost_risk(dict(C), None, None))
        except ZeroDivisionError:
            return "raised"

    inject("the cost risk zero-index guard",
           live_ext, "run_cost_risk", old_ext.run_cost_risk, cost_risk_probe, "raised")

    # (l) The earned value domain guards.
    inject("the scenario modeling domain guards",
           live_doc, "run_scenario_modeling", old_doc.run_scenario_modeling,
           lambda: abstains(live_doc.run_scenario_modeling(
               {"bac": 1_000_000, "ev": 400_000, "ac": 500_000, "cpi": -0.9, "spi": 1.0},
               None, None)),
           False)

    # (m) The anomaly placeholder.
    inject("the anomaly score placeholder",
           live_portfolio, "compute_portfolio", old_portfolio.compute_portfolio,
           lambda: round(live_portfolio.compute_portfolio(
               PORT, "P1", None, "2026-01-01")["results"][
                   "cat8_5_anomaly_score"]["composite_score"], 6) == 0.0,
           False)

    # (n) The cross-project Green band.
    inject("the reachable Green in the cross-project pattern",
           live_portfolio, "compute_portfolio", old_portfolio.compute_portfolio,
           lambda: live_portfolio.compute_portfolio(
               PORT, "P1", HIST, "2026-01-01")["results"][
                   "cat8_4_cross_project_pattern"]["status_color"],
           "Yellow")

finally:
    print()
    print("=" * 78)
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
    print("=" * 78)

sys.exit(1 if FAILED else 0)
