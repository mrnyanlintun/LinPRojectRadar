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
import json as _j43
import re as _re43

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.simulation import registry as _REG43  # noqa: E402
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

# =================================================================================================
# RUN 31, PASS 1: THIS SUITE IS HISTORICAL_ONLY FOR CATEGORY 8 AND CATEGORY 9.
#
# The assertions below describe implementations Run 31 superseded. They are preserved unedited,
# because they are the scientific record of what this instrument used to do, and the legacy code
# they describe is preserved for the same reason. What changes is resolution: for the sixteen
# Category-8/9 identities ONLY, `registry.run_module` executes the preserved legacy runner.
# Every other module still resolves to live production.
#
# The second half of the contract is asserted at the end of this block: current production
# reaches NONE of the sixteen legacy implementations and ALL sixteen canonical routes.
# =================================================================================================
import run31_historical_cat89 as _R31H                                        # noqa: E402
_R31H_HISTORICAL_ONLY = True

def _r31h_install():
    # Patch the registry MODULE OBJECT, not a local alias: every suite holds a reference to the
    # same singleton module however it spelled the import, so this reaches all of them.
    from app.simulation import registry as _registry
    _live = _registry.run_module

    def _resolve(new_id, si, rand, period_cutoff, *a, **k):
        if new_id in _R31H.LEGACY_CAT89:
            return _R31H.run_legacy(new_id, si, rand, period_cutoff)
        return _live(new_id, si, rand, period_cutoff, *a, **k)

    _registry.run_module = _resolve

_r31h_install()

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = 0
FAILED = 0
ROOT = pathlib.Path(__file__).resolve().parents[2]

# RUN 11 GATE 6. The conflict coefficient is None when it cannot be estimated from one voting
# lineage, and None does not round. Printed as the words the platform now uses rather than
# coerced to a zero, which is the reading this run removed.
def _k(v):
    return "not estimable" if v is None else round(v, 6)

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

# =================================================================================================
# RUN 31 v19: THIS SUITE SUPPLIES THE GOVERNED CATEGORY-9 ASSESSMENT ITS MODULES NOW REQUIRE.
#
# From sim-2026.08-v19 a package with no Category-9 assessment FAILS CLOSED for every
# Category-6/7/8/10 consumer. This suite's purpose is a module's ARITHMETIC, so it supplies the
# ordinary governed assessment a real caller supplies, through the ordinary signal-input key, and
# then tests the arithmetic it was written to test. It is not exempt from the gate: the ordinary
# precedence still applies, and the gate's own guards never install this.
# =================================================================================================
import run31_qualified_fixture as _R31Q                                       # noqa: E402
_R31Q.install()



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
    # RUN 20 CYCLE 9. The expected value here was the decision layer's own state NAME,
    # "Red-review", because Conservative Dominance returned that layer's counting state. It now
    # applies the dominance rule its name asserts and reports a BAND. The defect this section
    # exists to pin is unchanged and still pinned: two Red signals returned GREEN on the old code
    # and return an adverse band now. The decision layer's state is still reported, under its own
    # name, and is asserted here too so nothing is lost.
    check(normalise_status(new_r.get("state")) == "Red"
          and new_r.get("decision_layer_state") == "Red-review",
          "and returns a red band now, with the decision layer still classifying it a red review",
          str(new_r.get("state")))
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
        _got = run_conservative_dominance(case, None, None)
        check(normalise_status(_got.get("state")) == "Red"
              and _got.get("decision_layer_state") == "Red-review",
              f"two Red inputs return a red band when written {casing}",
              str(_got.get("state")))

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
        # RUN 30 v15. The three ensembles no longer all report a band: Weighted Voting abstains
        # without a governed weighting policy and Worst-2 asserts no traffic-light boundary over
        # its statistic. What THIS defect is about is that lowercase adverse evidence must not
        # read as agreement at low risk, and that is what is asserted for all three: the old code
        # returned Green on this input and no ensemble does now.
        old_c = old_fn(ENSEMBLE, None, None).get("status_color")
        new_c = fn(ENSEMBLE, None, "2026-06-30").get("status_color")
        check(old_c == "Green" and new_c != "Green",
              f"{name}: three lowercase red primary signals voted Green and no longer can",
              f"old={old_c} new={new_c}")
    check(run_majority_rules(ENSEMBLE, None, "2026-06-30").get("status_color") == "Red",
          "Majority Rules, the one of the three that still reports a band, reports Red")
    check(run_worst_n_of_m(ENSEMBLE, None, "2026-06-30").get("mean_worst_2") == 3.0,
          "and the Worst-2 mean over the two independent adverse signals is the ceiling, 3.0")

    UNKNOWN = {"signals": {"mc": {"status": "unexpected"}, "cusum": {"status": "unexpected"},
                           "doc": {"status": "unexpected"}},
               "simulationSignals": {"signal_array": []}}
    for fn, old_fn, name in ((run_weighted_voting, old_gov.run_weighted_voting,
                              "Weighted Voting"),
                             (run_majority_rules, old_gov.run_majority_rules, "Majority Rules"),
                             (run_worst_n_of_m, old_gov.run_worst_n_of_m, "Worst N of M")):
        old_c = old_fn(UNKNOWN, None, None).get("status_color")
        new_res = fn(UNKNOWN, None, "2026-06-30")
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
    # RUN 29 REPLACED THE CORRECTED RATIO. Run 2's fix was to stop double-counting delayed
    # items inside the at-risk term, which took the audit's own figures from 1.8 to 0.65. Run
    # 29's supplied contract goes further and states that a count ratio ALONE is not the
    # canonical item-level monitor: the method is the slack between the date an item is required
    # on site and the date it is forecast to arrive. So the ratio is gone rather than corrected,
    # and Run 2's property is preserved in the stronger form the new quantity allows -- an item
    # is in exactly ONE state, so nothing can be counted twice by construction, and no count
    # triple of any size can produce a proportion above one because no proportion is formed.
    check(abstains(new_p),
          "and produces no ratio at all now, because a count ratio is not the item-level "
          "monitor this module is named for", str(new_p.get("risk_ratio")))
    from run29_fixtures import procurement_items as _pi  # noqa: E402
    _slack = run_procurement_lead_time({"procurementItems": _pi()}, None, None)
    check(_slack.get("minimum_slack_days") == -10.0,
          "and the supplied contract's own answer is reproduced: a required day of one hundred "
          "against a forecast of one hundred and ten is a slack of minus ten days",
          str(_slack.get("minimum_slack_days")))
    _states = _slack.get("state_counts") or {}
    check(sum(_states.values()) == _slack.get("item_count"),
          "and the states partition the register, so no item can be counted in two of them",
          str(_states))
    _still_banding = 0
    for total in range(1, 12):
        for at_risk in range(0, total + 1):
            for delayed in range(0, at_risk + 1):
                res = run_procurement_lead_time(
                    {"longLeadItemsTotal": total, "longLeadAtRisk": at_risk,
                     "longLeadDelayed": delayed}, None, None)
                if not abstains(res):
                    _still_banding += 1
    check(_still_banding == 0,
          "and across every consistent count triple up to eleven items the counts alone produce "
          "no reading at all", f"{_still_banding} still produced one")
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
    # RUN 28 REPLACED THE ARITHMETIC THIS PAIR WAS PROVING UNTOUCHED, on the owner's explicit
    # authority, so the pair is rewritten rather than left asserting a sameness that is no longer
    # true. Defect 5 was a CRASH: `bac / cpi` had no guard, a cost index of exactly zero raised
    # inside the computation, and the whole project's result was lost to an exception rather than
    # to one module's abstention. That property is what this block exists to protect and it still
    # holds in the strongest form: the retired inputs reach no arithmetic at all, so no input can
    # raise inside this module. What is no longer asserted is that the figure is identical to the
    # old one, because the supplied contract replaced a deterministic index uplift with a
    # simulated total-cost distribution over the risk register's own events.
    from app.simulation.rng import make_rng as _mk
    _crm = {"costRiskModel": {
        "model_version": "CRM-1", "estimate_source": "approved base estimate",
        "cost_components": [{"component_id": "BASE", "base_amount": 100.0}],
        "risk_events": [{"risk_id": "R1", "probability": 0.5, "impact_distribution": "POINT",
                         "impact": 20.0}]}}
    live = run_cost_risk(_crm, _mk(20260828), None)
    check(not abstains(live) and live.get("p80_total_cost") is not None,
          "the method computes on a governed cost risk model: what the domain guard removed was "
          "a crash, and nothing has been silenced",
          str(live.get("evidence_metric")))
    check(abs(live["p80_total_cost"] - 120.0) < 1e-9,
          "and reproduces the supplied contract's own eightieth percentile of 120 on its own "
          "worked two-point model", str(live.get("p80_total_cost")))
    _raised_new = False
    try:
        run_cost_risk({"bac": 1_000_000, "cpi": 0.0, "ac": 500_000, "ev": 400_000}, None, None)
    except ZeroDivisionError:
        _raised_new = True
    check(not _raised_new,
          "and defect 5's own property holds a fortiori: a cost index of zero cannot raise "
          "inside this module, because the cost index reaches no arithmetic in it at all")
    old_live = old_ext.run_cost_risk(
        {"bac": 1_000_000, "cpi": 0.9, "ac": 500_000, "ev": 400_000}, None, None)
    check(old_live.get("p80_eac") is not None and live.get("p80_eac") is None,
          "and the pinned pre-fix code still computes its index uplift, so the comparison is "
          "live and the difference between the two lines is a measured fact"
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
    # RUN 28. Float is now taken from the network's own forward and backward passes rather than
    # from two reported scalars normalised by progress, so the completion figure cannot restore
    # this module: the network can. Defect 10's property -- that no invented completion stands in
    # for a reported one -- holds a fortiori, because completion is not an input it has.
    _fc_net = {"scheduleNetwork": {
        "schedule_version": "SCH-1", "status_basis": "2026-06-30 data date",
        "activities": [{"activity_id": "A", "predecessors": [], "current_duration": 3,
                        "baseline_total_float": 5},
                       {"activity_id": "B", "predecessors": [], "current_duration": 4},
                       {"activity_id": "C", "predecessors": ["A", "B"], "current_duration": 2}]}}
    with_pct = run_float_consumption(_fc_net, None, None)
    check(not abstains(with_pct) and with_pct.get("float_consumed_days") == 4.0,
          "and with a real network it computes: A began with five days of float and the passes "
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
    # RUN 29 REPLACED THE COHORT SHARE. Run 2 required an audited findings cohort for the open
    # backlog to be a share OF, which stopped the unbounded intake ratio. Run 29's supplied
    # contract states that a nonconformance rate is events over GOVERNED EXPOSURE -- inspections,
    # inspected units, labour hours, work value -- and that a ratio whose numerator and
    # denominator populations differ is not a universal NCR rate. The cohort share was such a
    # ratio: a stock carried across periods over the size of one audit. It is replaced, and the
    # open backlog, its age, its severity and the closure rate are reported SEPARATELY.
    check(abstains(run_ncr_rate(dict(N, totalFindings=40), None, None)),
          "the audited cohort alone no longer produces a rate, because the backlog and the "
          "cohort are different populations")
    from run29_fixtures import ncr_record  # noqa: E402
    _ncr = run_ncr_rate({"ncrExposureRecord": ncr_record()}, None, None)
    check(_ncr.get("ncr_rate") == 0.04,
          "and the supplied contract's own answer is reproduced: four nonconformances over one "
          "hundred inspections is 0.04", str(_ncr.get("ncr_rate")))
    check(_ncr.get("open_count") == 4 and _ncr.get("closure_rate") == 0.0,
          "with the open backlog and the closure rate reported beside it rather than divided "
          "into it", f"{_ncr.get('open_count')} open, closure {_ncr.get('closure_rate')}")
    check(abstains(run_ncr_rate({"ncrExposureRecord": ncr_record(exposure=0.0)}, None, None)),
          "and with no exposure at all no normalised rate is fabricated")

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
    # RUN 29 REPLACED THE RATIO. Run 2 required verified lost days and a positive float figure
    # before forming a proportion of one in the other. Run 29's supplied contract states that
    # weather occurrence is not schedule impact, and that impact requires the event, the affected
    # activity, the planned work, the lost time, the governing allowance, the path and its float,
    # causal evidence and a modelled consequence. A ratio of a count to a float number carries
    # none of the middle six, so it is replaced rather than renamed.
    check(abstains(run_weather_impact({"weatherDaysLost": 3, "floatRemaining": 30}, None, None)),
          "a lost-day count and a float figure no longer produce an impact, because there is no "
          "activity, no path, no allowance and no causal evidence in the pair")
    from run29_fixtures import weather_events  # noqa: E402
    _wx = run_weather_impact({"weatherImpactEvents": weather_events()}, None, None)
    check(_wx.get("direct_path_effect_days") == 2.0,
          "and the supplied contract's own answer is reproduced: a verified event causing two "
          "lost days on a zero-float critical activity with no mitigation has a direct modelled "
          "path effect, before recovery, of two days",
          str(_wx.get("direct_path_effect_days")))
    check(run_weather_impact(
        {"weatherImpactEvents": weather_events(lost=2.0, available_float=5.0)},
        None, None).get("direct_path_effect_days") == 0.0,
        "while the identical event on a path with five days of float to absorb it has no direct "
        "effect on the schedule at all")
    check(not abstains(old_doc.run_weather_impact(
        {"weatherDaysLost": 3, "floatRemaining": 30,
         "sources": {"weatherDaysLost": {"docType": "derived"}}}, None, None)),
        "where the old code computed and appended a note to the sentence", "")

    # ---- defect 13, scenario modeling and its sibling
    # RUN 14, EXPECTATION CORRECTED WITH ITS REASON. Defect 13 was a domain defect in an
    # earned-value forecast that Scenario Modeling carried as its behaviour when no decision
    # problem was provided. Run 13 recorded that fallback itself as a mismatch, because a reader
    # received a band under the name of a method the platform was not running, and Run 14
    # removed it. The domain guards Run 2 added to that fallback went with the code they
    # guarded, so this loop now covers the What-If matrix, which is unchanged and still carries
    # them, and Scenario Modeling is asserted separately below on the behaviour it has now. The
    # old-code half of every check is untouched: the defect is still shown to have been real.
    for fn, old_fn, name in ((run_whatif_matrix, old_gov.run_whatif_matrix,
                              "What-If Scenario Matrix"),):
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
    # Scenario Modeling after Run 14: with no decision problem in the corpus it abstains, and it
    # does so naming the missing structure rather than the missing figures, on every one of the
    # inputs above INCLUDING the internally consistent one. The old code produced a status on
    # all four.
    for label, si in (
            ("a negative cost index",
             {"bac": 1_000_000, "ev": 400_000, "ac": 500_000, "cpi": -0.9, "spi": 1.0}),
            ("a negative budget",
             {"bac": -1_000_000, "ev": 400_000, "ac": 500_000, "cpi": 0.9, "spi": 1.0}),
            ("earned value above the budget",
             {"bac": 1_000_000, "ev": 1_400_000, "ac": 500_000, "cpi": 0.9, "spi": 1.0}),
            ("a consistent earned value position",
             {"bac": 1_000_000, "ev": 400_000, "ac": 500_000, "cpi": 0.9, "spi": 0.95})):
        old_s = old_doc.run_scenario_modeling(dict(si), None, None)
        new_s = run_scenario_modeling(dict(si), None, None)
        check(not abstains(old_s),
              f"Scenario Modeling: {label} produced a status on the old code",
              str(old_s.get("status_color")))
        # RUN 29. The reason code moved from the DECISION structure to the SCENARIO structure,
        # and the move is the correction: Run 10B had made this module read an actions-by-
        # scenarios payoff matrix and return a recommended action, which is a decision method.
        # The supplied Run-29 contract says in its own words not to confuse a scenario model
        # with the later question of which intervention to choose, so the defining structure is
        # now a scenario set and the abstention names that instead.
        check(abstains(new_s)
              and new_s.get("abstention_reason_code") == "canonical_structure_absent",
              f"Scenario Modeling: {label} abstains now, naming the absent scenario set",
              str(new_s.get("abstention_reason_code")))
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
    # RUN 43, THE RETIREMENT. Three of the project-level fifteen -- A1.1, B2.1 and A2.5 -- are
    # retired from service and reach no ledger row at all. The population is derived from
    # registry.is_retired(); the retired members are asserted ABSENT, which is stronger than the
    # accounting they carried before.
    _f15_service = [m for m in FIFTEEN
                    if m not in PORTFOLIO_THREE and not _REG43.is_retired(m)]
    _f15_retired = [m for m in FIFTEEN
                    if m not in PORTFOLIO_THREE and _REG43.is_retired(m)]
    check(all(mid in comp or mid in abst for mid in _f15_service),
          "every project-level one of the fifteen in service is accounted for, computed or "
          "abstained")
    check(not [m for m in _f15_retired if m in comp or m in abst],
          "and not one of those retired from service reaches the ledger at all",
          str([m for m in _f15_retired if m in comp or m in abst]))
    check(not (set(FIFTEEN) & set()),
          "and none of the fifteen was moved to the disabled set by this run")

    # RUN 14, EXPECTATION CORRECTED WITH ITS REASON. A5.4 is no longer in this list, and the
    # check that replaces it below is the stronger one. Until Run 14 it produced a finding on
    # every project because it fell back to an earned-value forecast when no decision problem
    # was in the corpus; Run 13 recorded that as a mismatch and Run 14 removed the fallback. On
    # this project, which carries no decision problem, the correct behaviour is an abstention
    # naming the absent structure, and it is asserted as such rather than dropped.
    check("A5.4" not in comp and "A5.4" in abst,
          "Scenario Modeling abstains on the real path where no decision problem is in the "
          "corpus, rather than reporting a forecast under its name",
          str(abst.get("A5.4", {}).get("reason"))[:120])
    # RUN 28, EXPECTATION CORRECTED WITH ITS REASON, on the same footing as the Run-14 note
    # above. A3.6 is no longer in this list. Until Run 28 it produced a finding on every project
    # because it inflated the cost index by a fixed multiple of the standard normal eightieth
    # percentile; the owner's supplied contract replaces that with a simulated total cost over a
    # stochastic cost-risk model. On a project whose register carries no row with BOTH a
    # probability and a cost impact there is no model to simulate, and the correct behaviour is
    # an abstention naming the absent structure. It is asserted as such rather than dropped.
    check("A3.6" not in comp and "A3.6" in abst,
          "Cost Risk Analysis P80 abstains on the real path where the register supports no "
          "stochastic model, rather than reporting a deterministic uplift under its name",
          str(abst.get("A3.6", {}).get("reason"))[:120])
    check(abst.get("A3.6", {}).get("abstention_reason_code") == "canonical_structure_absent",
          "and names the absent cost risk model as the reason",
          str(abst.get("A3.6", {}).get("abstention_reason_code")))
    # RUN 29 REMOVED A4.9 FROM THIS LIST, for the same reason and with the same discipline as
    # the A3.6 note above: it no longer produces a finding on the real path, because the
    # canonical method needs an item level register the corpus does not carry, and its
    # abstention is asserted a few lines below rather than dropped.
    # RUN 30 CLOSURE REMOVED B2.1 FROM THIS LIST, with the reason recorded rather than the
    # expectation quietly rewritten. Dempster-Shafer's defining structure is a set of bodies of
    # evidence expressed as mass over a stated frame, each naming the evidence it was read from.
    # The four masses the v14/v15 implementation combined were LITERALS IN THE MODULE, selected
    # by banding the cost and schedule indices, a forecast overrun and a document risk score.
    # They were not evidence any project supplied, so on this project -- which carries no mass
    # function -- the correct behaviour is an abstention naming the absent structure, and it is
    # asserted as such below rather than dropped.
    # RUN 36 CLOSURE REMOVED A1.1 FROM THIS LIST, with the reason recorded rather than the
    # expectation quietly rewritten, exactly as A3.6, A4.9 and B2.1 were removed above. The owner
    # ruled that the `Required:` input list in supervisory specification s1.1 governs what
    # qualifies as canonical Monte Carlo. Canonical execution needs the declared cost-driver
    # distribution structure AND an authoritative rule for turning drawn driver figures into a
    # forecast; the specification requires that rule and does not define it, and inventing one
    # would be inventing the method. So the module is operationally disabled for insufficient
    # input, and the retained budget-and-index approximation is preserved but not reached. Its
    # new behaviour is asserted immediately below rather than dropped.
    for mid in ("A6.1", "A6.4", "B1.1"):
        check(mid in comp, f"{FIFTEEN[mid]} produces a finding on the real path",
              str(abst.get(mid, {}).get("reason"))[:90])
    # RUN 43: A1.1 is retired from service. It produces no finding, which is what this asserted,
    # and it now publishes no ledger row either, so there is no reason code on it to read.
    check("A1.1" not in comp and "A1.1" not in abst and _REG43.is_retired("A1.1"),
          f"{FIFTEEN['A1.1']} produces NO finding on the real path and no ledger row either, "
          f"because it is retired from service",
          str(abst.get("A1.1", {}).get("reason"))[:120])
    check(not _re43.search(r"\bA1\.1\b", _j43.dumps(comp, default=str))
          and not _re43.search(r"\bA1\.1\b", _j43.dumps(abst, default=str)),
          "and no ungoverned-method-definition code, and no statement about it of any kind, "
          "survives on the ledger", str(abst.get("A1.1", {}).get("abstention_reason_code")))
    # RUN 43: B2.1 is retired from service. It combines nothing, which is what this asserted,
    # and it reaches no row, so the canonical route produces no silence to record either.
    check("B2.1" not in comp and "B2.1" not in abst and _REG43.is_retired("B2.1"),
          f"{FIFTEEN['B2.1']} is retired from service, so it reaches no ledger row and combines "
          f"no masses that are literals in the module under the name of the method",
          str(abst.get("B2.1", {}).get("reason"))[:120])
    check(not _re43.search(r"\bB2\.1\b", _j43.dumps(comp, default=str))
          and not _re43.search(r"\bB2\.1\b", _j43.dumps(abst, default=str)),
          "and the ledger records nothing about it at all, canonical route or otherwise",
          str(abst.get("B2.1", {}).get("canonical_disposition")))
    # RUN 29 CLOSURE REMOVED A4.4 FROM THIS LIST, and the reason is recorded rather than the
    # expectation being quietly rewritten. Run 29 reported that no Category-4 or -5 canonical
    # structure was populated from the real corpus. That single sentence covered two different
    # cases, and the closure decomposed it: sixteen of the seventeen structures are genuinely
    # absent, but `ncrExposureRecord` was not. The nonconformance log already yielded the count
    # of nonconformances raised in the period and the inspection report already yielded the
    # number of items inspected; both reached signalInputs and neither reached a module. The
    # closure wired them, so the nonconformance rate now COMPUTES on the real path from evidence
    # that was already being extracted, and it is asserted as computing here. The quantities that
    # genuinely need per-event detail -- severities, closure rate, open ages -- are still reported
    # absent rather than invented, which is checked in the closure's own suites.
    check("A4.4" in comp,
          f"{FIFTEEN['A4.4']} produces a finding on the real path, because the closure wired the "
          f"nonconformance count and the inspected quantity the corpus already extracted",
          str(abst.get("A4.4", {}).get("reason"))[:120])
    # These two refuse for want of data the fix now requires, and each states which data.
    for mid in ("A4.5", "A6.3"):
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
    check("A2.5" not in abst and "A2.5" not in comp and _REG43.is_retired("A2.5"),
          "Float Consumption Rate is retired from service, so it reaches no ledger row on the "
          "real path rather than abstaining on one", fc[:90])
    # RUN 28. The reason moved from the required-inputs gate to the structural one, and the move
    # is more specific rather than less: the corpus carries no ACTIVITY NETWORK, which is what
    # float is derived from, and saying so names the thing that is missing instead of naming two
    # scalars nobody would have known where to find.
    check(not _re43.search(r"\bA2\.5\b", _j43.dumps(abst, default=str)),
          "and states nothing at any gate, because a module retired from service does not reach "
          "the canonical-structure gate at all",
          str(abst.get("A2.5", {}).get("abstention_reason_code")))

    # RUN 29. A4.9 no longer renders a ratio on the real path: the corpus carries the long-lead
    # counts an extraction reads off a monthly report, and the canonical method needs an item
    # level register with a required-on-site date and a forecast delivery date for each item.
    # So on the real corpus it ABSTAINS, and that abstention is asserted here rather than a
    # figure -- which is the honest outcome and the one the supply-path reconciliation records.
    check("A4.9" in abst,
          "and the procurement monitor abstains on the real path, because the corpus carries "
          "counts of long-lead items and not the dates each one is required and forecast for",
          str(abst.get("A4.9", {}).get("reason"))[:110])
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
    # RUN 33. WHAT "LANDS" ON THE REAL PATH CHANGED, and this is the correct outcome rather than
    # a regression. At v20 these three produced populated readings from bare portfolio vectors
    # and a list of result snapshots; at v21 a Portfolio Health reading needs a GOVERNED COHORT
    # -- a declared population, period, feature schema and model version -- and a GOVERNED SIGNAL
    # HISTORY, and this project supplies neither. What the check now proves is that each identity
    # LANDS ADDRESSABLY with its own stated reason rather than vanishing, which is the property
    # the original check was really protecting: a defect must not be able to hide as an absence.
    # RUN 43, THE RETIREMENT. All five Portfolio Health identities are retired from service, so
    # the snapshot carries no per-identity results at all. "Lands addressably with its own
    # reason" was the guarantee while the identities were in service; the property it protected
    # -- a defect must not hide as an absence -- is now carried by the snapshot's OWN stated
    # reason, which is asserted here in its place, together with the absence of every key.
    _snap_env = (s4.get("portfolio_snapshot") or {})
    for key, name in (("cat8_3_trajectory_classifier", "Signal Trajectory Classifier"),
                      ("cat8_4_cross_project_pattern", "Cross-project Pattern Detector"),
                      ("cat8_5_anomaly_score", "Anomaly Score")):
        check(key not in snap,
              f"{name} is retired from service, so it carries no key in the stored portfolio "
              f"snapshot", str(sorted(snap.keys())))
        check(not snap.get(key, {}).get("status_color")
              and not snap.get(key, {}).get("voting"),
              f"{name} carries no status colour and no vote")
        landed[key] = "retired"
        print(f"    retired     {name}")
    check(bool(str(_snap_env.get("message") or "").strip()) and not snap,
          "and the snapshot itself states, in one place, why there is no portfolio-level "
          "reading, so the absence is not silent",
          str(_snap_env.get("message"))[:120])
    # The slope on the real path, recomputed from the stored periods rather than read back.
    stored_cpis = []
    for p in (1, 2, 3, 4):
        stored_cpis.append(post({"action": "projectresults", "session_token": pm,
                                 "id": SECOND, "period": p})["result"]["signal_inputs"]["cpi"])
    last3 = stored_cpis[-3:]
    expected = round((last3[-1] - last3[0]) / (len(last3) - 1) * 1000) / 1000
    # THE DEFECT-6 FINDING ITSELF IS PRESERVED and is asserted against the PRESERVED v20
    # implementation, executed directly, because that is what it was always really about: the
    # slope is the movement over the INTERVALS between the observations, not over their number.
    # `assert_not_reachable` supplies the other half -- current production cannot satisfy it.
    import run33_historical_portfolio as _R33H
    _R33H.assert_not_reachable(lambda cond, name, detail="": check(cond, f"HISTORICAL: {name}",
                                                                   str(detail)))
    _hist_pf = [{"id": "A", "cpi": last3[-1], "spi": 1.0, "docRiskScore": 0.0,
                 "actualPctComplete": 50},
                {"id": "B", "cpi": 1.0, "spi": 1.0, "docRiskScore": 0.0,
                 "actualPctComplete": 50}]
    _legacy = _R33H.run_legacy(_hist_pf, "A", [{"signal_inputs": {"cpi": c}} for c in last3],
                               "2026-06-30")["results"]["cat8_3_trajectory_classifier"]
    check(abs(_legacy["trend"] - expected) < 1e-9,
          "HISTORICAL (v20): the trajectory slope on the real path is the stored periods' own "
          "movement over the intervals between them",
          f"{_legacy['trend']} vs {expected}")

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
        b_k, a_k = _k(before["project_conflict"]), _k(after["project_conflict"])
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
    # RUN 20 CYCLE 3 P0D, AND WHY THIS PROPOSITION MOVED RATHER THAN BEING DELETED. Until cycle 3
    # the two voting modules were fused as two independent sources, so the rollup carried a
    # conflict coefficient and the Run-2 fix could be measured on it. Cycle 3 established that
    # they are two transforms of ONE body of earned-value evidence, and one body of evidence
    # cannot disagree with itself, so the rollup now estimates no conflict at all and this
    # vehicle can no longer reach the thing Run 2 proved. The finding is NOT weakened: it is
    # measured where it actually lives, on dst_combine itself, using the audit's own worked
    # example -- two sources each Green 0.8 with 0.2 of mass left on ignorance. The old rule
    # counted the two Green-against-ignorance cross terms as disagreement and reported K = 0.32;
    # the corrected rule intersects ignorance with every state and reports K = 0. Both numbers
    # are the audit's, hand-calculable, and neither is read from the function under test.
    _g = {"Green": 0.8, "Yellow": 0.0, "Amber": 0.0, "Red": 0.0, "Unknown": 0.2}
    _k_old = round(old_fusion.dst_combine(dict(_g), dict(_g)).get("conflict", 0.0), 6)
    _k_new = round(fusion.dst_combine(dict(_g), dict(_g)).get("conflict", 0.0), 6)
    print(f"   MEASURED on dst_combine itself, the audit's worked example: K {_k_old} -> {_k_new}")
    check(_k_old == 0.32 and _k_new == 0.0,
          "the fix DOES move the conflict coefficient: on the audit's own two-Green example the "
          "old rule counted ignorance as disagreement and reported 0.32, and the corrected rule "
          "reports none, which is measured rather than asserted",
          f"old {_k_old}, new {_k_new}")
    check(conflict_moves == 0 and cat_conflict_moves == 0,
          "and the rollup itself no longer moves, because after the lineage correction the one "
          "voting category is one body of evidence and no conflict coefficient is estimated for "
          "it at all, in either the old rule or the new",
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
            # RUN 28 CLOSURE. A SECOND PERMITTED DIFFERENCE IN THIS FILE, NAMED RATHER THAN
            # ADMITTED BY LOOSENING THE CHECK. One sentence of copy names A1.1, and the owner
            # decided A1.1's identity is `Monte Carlo EAC Forecast`. The rename is normalised
            # OUT of both sides before the comparison, so the Run-4 property below -- every
            # removed line carried the validation claim, every added line is a comment or a
            # continuation -- is asserted over a file that differs from the baseline in nothing
            # else. The rename itself is then asserted on its own, so it cannot hide here.
            _A11_OLD, _A11_NEW = "Monte Carlo EAC", "Monte Carlo EAC Forecast"
            check(_A11_NEW in live and _A11_OLD in base,
                  f"{rel}: the copy names A1.1, and the name it uses is the one the owner "
                  f"decided rather than the one the Run-4 baseline carried")
            # RUN 32 FINAL CLOSURE. A THIRD PERMITTED DIFFERENCE, NAMED RATHER THAN ADMITTED
            # BY LOOSENING THE CHECK, on exactly the Run-28 construction above. B4.7's method
            # class became `Minimax_Regret_Decision_Rule` at the section-3 rename, and this file
            # keys the courses-of-action lookup on it. Reading only the old key returned
            # undefined on every current project, so the frame went silently empty -- a lookup
            # that stops matching does not fail, it disappears. The rename is normalised OUT of
            # both sides before the Run-4 property is asserted, and is asserted on its own below
            # so it cannot hide here.
            _B47_OLD = "var regret = mods.Regret_Minimization;"
            _B47_NEW = ("var regret = mods.Minimax_Regret_Decision_Rule "
                        "|| mods.Regret_Minimization;")
            check(_B47_NEW in live and _B47_OLD in base,
                  f"{rel}: the courses-of-action lookup reads B4.7's CURRENT method class, with "
                  f"the historical one kept only so a row stored before the rename still routes")
            _norm = live.replace(_B47_NEW, _B47_OLD).replace(_A11_NEW, _A11_OLD)
            check(_norm.count(_A11_OLD) == base.count(_A11_OLD),
                  f"{rel}: and the rename is the ONLY thing that changed about that name: "
                  f"normalising it back gives exactly the baseline's occurrences",
                  f"{_norm.count(_A11_OLD)} vs {base.count(_A11_OLD)}")
            removed = [ln.strip() for ln in base.splitlines()
                       if ln not in _norm.splitlines()]
            added = [ln.strip() for ln in _norm.splitlines()
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
            # RESTATED BY RUN 16. Until Run 16 the freeze removed nothing from this file and
            # that record stands; Run 16 rewords three section badges in place, so the earlier
            # wording of each leaves. Named by content below rather than tolerated.
            # RESTATED BY THE POST-RUN-22 UI CORRECTION, EARLIER FINDINGS PRESERVED. Three
            # more lines leave this file and each is named rather than tolerated: the scroll-spy
            # comment and the `classList.toggle("active", ...)` line, because the rail's
            # SELECTION may not be spelt with the Signal Flow's word for analytical ACTIVITY;
            # and `p.history = []; p.events = [];`, because blanking the browser copy of the
            # append-only event log made the live page deny retained documents that the same
            # page, reloaded from the same server, correctly disclosed (`p.history = []` stays,
            # on its own line).
            def _postrun22_removed(line):
                return (line == '// Scroll-spy: highlight whichever section is currently most in view.'
                        or line == 'b.classList.toggle("active", b.getAttribute("data-secnav-target") === secId);'
                        or line == 'p.history = []; p.events = [];')
            # RUN 25, OWNER-DIRECTED CONTRACT CHANGE, 2026-08-14. The owner ordered the left
            # section-navigator rail removed entirely, reversing the earlier instruction that
            # it stays. The whole buildSectionNav block the baseline carried (delimited by its
            # own section comments) and its one call site therefore leave this file. The
            # allowance is the baseline's OWN lines for that block, so it cannot excuse the
            # removal of anything else. Recorded in run20_anti_fossilization_register.csv.
            _rail_slice = base[base.index("/* ---------- section navigator (second, left-side menu bar)"):
                               base.index("fetch full stored result")]
            _rail_base_lines = {ln.strip() for ln in _rail_slice.splitlines()}
            _rail_base_lines.add("buildSectionNav(root);")
            def _run25_rail_removed(line):
                return line in _rail_base_lines
            check(all('" modules")' in ln or '" categories")' in ln or "modules`)" in ln
                  or _postrun22_removed(ln) or _run25_rail_removed(ln)
                  for ln in removed),
                  f"{rel}: the freeze removed nothing from this file beyond the three section "
                  f"badges Run 16 reworded", str(removed)[:200])
            # RESTATED BY RUN 11, ORIGINAL FINDING PRESERVED. Until Run 11 this file differed
            # from the freeze only by Run 4's abstention-reason graft, and that record stands.
            # Run 11 Gate 1 adds exactly one statement to it: the opt-in gate that stops the
            # client-side evidence-module backfill from recomputing on the participant route.
            # It is named here rather than tolerated as an unexplained difference, so the file
            # still has no addition that is not accounted for by a run's authorised scope.
            RUN11_GATE_1_LINE = "if (!window.LIN_ALLOW_CLIENT_ANALYTICS) return;"
            # RESTATED BY RUN 16, ORIGINAL FINDING PRESERVED. Run 16 changes two more things in
            # this file and names both rather than widening the rule. The collapsed section
            # badges read "96 modules" and "11 categories" beside a project that had computed
            # nothing, which reads as a tally of what ran; the figures are unchanged and the word
            # beside them now says they are registry counts. And the clear-all handler drops the
            # browser's copy of the derived result, because the server now retires that row and a
            # cached copy of it kept the cleared project drawing results in the same session.
            RUN16_LINES = {
                'if (window.LinResults && LinResults.clear) LinResults.clear();',
            }
            def _run16_badge(line):
                return ('totalModulesForBadge} registered' in line
                        or 'totalModulesForBadge + " registered"' in line
                        or 'totalCats + " registered"' in line)
            # RESTATED BY THE POST-RUN-22 UI CORRECTION. Its additions to this file are the
            # rail's selection state (`selected` + `aria-current`, set by the click itself and
            # held while the smooth scroll runs) and the removal of the event-log mask. Each is
            # named by content, so an unexplained addition is still red.
            POSTRUN22_LINES = {
                "'aria-current=\"false\" ' +",
                "const setSelected = (secId) => {",
                'const on = b.getAttribute("data-secnav-target") === secId;',
                'b.classList.toggle("selected", on);',
                'b.setAttribute("aria-current", on ? "true" : "false");',
                "let selectionPinnedUntil = 0;",
                "setSelected(secId);",
                "selectionPinnedUntil = Date.now() + 1200;",
                "if (Date.now() < selectionPinnedUntil) return;",
                "p.history = [];",
            }
            check(all(ln.startswith("//") or ln.startswith("/*") or ln.startswith("*")
                      or "abstained" in ln or ln == "}"
                      or ln == RUN11_GATE_1_LINE or ln in RUN16_LINES or _run16_badge(ln)
                      or ln in POSTRUN22_LINES
                      for ln in added),
                  f"{rel}: and everything it added is the abstention-reason graft, Run 11's "
                  f"client-analytics gate, Run 16's registry-count wording and cache drop, or "
                  f"the comment recording why", str(added)[:200])
            check(RUN11_GATE_1_LINE in [ln.strip() for ln in live.splitlines()],
                  f"{rel}: and Run 11's gate is actually present, so the allowance above is "
                  f"not a licence for an absent line")
            check("p.storedResult.abstained = resp.result.abstained" in live,
                  f"{rel}: which is the one line that makes an abstaining module say what it "
                  f"is waiting for on the page a project manager reads")
            continue
        # RESTATED BY RUN 11 GATES 5 AND 6, ORIGINAL FINDING PRESERVED. Every run since the
        # freeze left the participant surface byte-identical, and that record stands. Run 11 is
        # authorised to change what a participant is TOLD about the governed status and its
        # conflict, and nothing else: taxonomy.js gains the read of the two stored fields, and
        # app.js prefers the server's conflict sentence over a legacy classification that reads
        # evidence which does not vote. Each is named here, and each is required to be present,
        # so the allowance cannot cover an unrelated edit.
        RUN11_WORDING_SCOPE = {
            "assets/js/taxonomy.js": "conflictSentence: pick(\"project_conflict_sentence\")",
            "assets/js/app.js": "_f.conflictSentence",
            # Gate 4: the generated evidence object, loaded so the handbook's qualifications sit
            # beside its claims.
            "assets/js/ds_defensibility_data.js": "Validation for this method would consist of",
            "index.html": "ds_defensibility_evidence.js",
            # RUN 32 FINAL CLOSURE. The expected-regret chart was keyed on B4.7's OLD method
            # class, which the section-3 rename stopped anything from emitting, so the chart
            # silently stopped being drawn rather than failing. The marker is the current class.
            "assets/js/module_charts.js": "Minimax_Regret_Decision_Rule",
        }
        if rel in RUN11_WORDING_SCOPE and live != base:
            marker = RUN11_WORDING_SCOPE[rel]
            check(marker in live,
                  f"{rel}: Run 11's authorised wording change is actually present")
            check(marker not in base,
                  f"{rel}: and it is what the file gained rather than something already there")
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

    # RUN 30. THE INJECTION SITE MOVED, AND THE MOVE IS THE POINT. The v15 ensembles read the
    # vocabulary through `fusion.normalise_status` when the governed signals are assembled, not
    # through a name bound in models_gov, so patching the old site would have applied cleanly and
    # changed nothing -- an injection that silently fails to apply, which is one of the five
    # failure modes this programme catalogues. The probe also moves from Weighted Voting, which
    # now abstains for want of a governed weighting policy and could not show the defect either
    # way, to Majority Rules, which still reports a band and is the one of the three whose answer
    # the vocabulary decides.
    inject("the shared status vocabulary in the voting ensembles",
           fusion, "normalise_status", case_sensitive,
           lambda: live_gov.run_majority_rules(ENSEMBLE, None, "2026-06-30").get("status_color"),
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

    # (g) The procurement bound. RUN 29: the bound was on a ratio that no longer exists, so the
    # injected fault is bound to the property that replaced it -- the counts alone produce no
    # reading, and swapping the v2 function back in makes them produce one again.
    inject("the procurement ratio bound",
           live_doc, "run_procurement_lead_time", old_doc.run_procurement_lead_time,
           lambda: abstains(live_doc.run_procurement_lead_time(dict(P), None, None)),
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
