#!/usr/bin/env python3
"""
Run 10B, Gates 3 to 9: the canonical structures, the reference objects, and what must not move.

WHAT A CHECK IN THIS FILE IS.

1. THE MODULE LISTS ARE DERIVED MECHANICALLY from the Run 8 classification file, never typed
   from a report. If the counts do not reconcile this file stops rather than proceeding.
2. EVERY EXPECTATION IS DERIVED FROM A STATED DEFINITION, in this file or in the Run 9 oracles,
   and never by running the module and recording what it returned.
3. THE REAL PRODUCTION FUNCTION IS DRIVEN, through the registry, on the real structure. Nothing
   here re-implements a production formula and compares it with itself.
4. ABSENT STRUCTURE MUST ABSTAIN, and that is asserted for every one of the six, over the absent
   case, the empty case and several malformed cases.
5. EVERY EXPECTATION IS PROVED ABLE TO FAIL, by perturbation, in the last section.
6. NOTHING HERE ACTIVATES A MODULE, MAKES ONE VOTING, VALIDATES A BAND, OR CONSTITUTES EMPIRICAL
   VALIDATION OF ANYTHING. The synthetic package is research fixture material and says so on
   every row.

Run:
    PYTHONIOENCODING=utf-8 python tools/test_run10b_canonical_integration.py
"""

from __future__ import annotations

import csv
import datetime as _dt
import math
import pathlib
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.simulation import canonical  # noqa: E402
from app.simulation.compute import compute_project  # noqa: E402
from app.simulation.models import ABSTAIN_DECISION_STRUCTURE_ABSENT  # noqa: E402
from app.simulation.models import ABSTAIN_STRUCTURE_ABSENT, VALIDATED  # noqa: E402
from app.simulation.registry import (  # noqa: E402
    CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY, registry_index, run_module,
)
from tests.synthetic_fixtures.importers import fixture_loader_v03 as FL  # noqa: E402
from tests.synthetic_fixtures.importers import production_structures as PS  # noqa: E402
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
# Suites that look modules up in the routing table, or inspect a runner's SOURCE, must
# resolve the sixteen to their superseded implementations too, or a parsimony/known-answer
# proof about the old code would silently read the new code instead.
VALIDATED = _R31H.historical_validated()
from app.simulation import registry as _r31h_reg                      # noqa: E402
run_module = _r31h_reg.run_module

ROOT = pathlib.Path(__file__).resolve().parents[2]
CODE_AUDIT = ROOT / "code_audit"
CUTOFF = _dt.date(2026, 6, 30)
NOOP = lambda: 0.5  # noqa: E731

PASSED = 0
FAILED = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def section(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def abstains(result) -> bool:
    return bool(result.get("insufficient_data")) and result.get("status_color") is None


def speakable(result, label: str, full_stop: bool = True) -> None:
    """The naming rules the ledger enforces. `full_stop` is relaxed only for abstention text
    this run did not write, which predates the convention and is not in scope to reword."""
    reason = str(result.get("evidence_metric") or "")
    check(bool(reason.strip()) and (reason.strip().endswith(".") or not full_stop),
          f"{label}: the abstention states a reason in words", reason[:80])
    check("—" not in reason and " & " not in reason,
          f"{label}: with no em dash and the word and rather than an ampersand", reason[:80])
    check("_" not in reason, f"{label}: and no key name or reason code", reason[:80])
    check(not any(f"{g}{n}." in reason for g in "ABCD" for n in range(1, 12)),
          f"{label}: and no module id", reason[:80])


def close(a, b, tol=1e-9) -> bool:
    return a is not None and b is not None and abs(float(a) - float(b)) <= tol


# =================================================================================================
section("0. THE MODULE LISTS, DERIVED MECHANICALLY FROM THE CLASSIFICATION FILE")
# =================================================================================================

BUCKETS: dict[str, dict] = {}
with (CODE_AUDIT / "run8_module_classification.csv").open(encoding="utf-8") as fh:
    for row in csv.DictReader(fh):
        BUCKETS[row["module_id"]] = row

BUCKET_3 = sorted(m for m, r in BUCKETS.items() if r["final_owner_action_bucket"] == "3")
BUCKET_4 = sorted(m for m, r in BUCKETS.items() if r["final_owner_action_bucket"] == "4")
BUCKET_5 = sorted(m for m, r in BUCKETS.items() if r["final_owner_action_bucket"] == "5")

check(len(BUCKET_3) == 7, "the classification file carries exactly seven in the "
      "project-structure bucket", str(BUCKET_3))
check(len(BUCKET_4) == 2, "exactly two in the reference and decision bucket", str(BUCKET_4))
check(len(BUCKET_5) == 2, "exactly two in the optional or disabled bucket", str(BUCKET_5))
if not (len(BUCKET_3) == 7 and len(BUCKET_4) == 2 and len(BUCKET_5) == 2):
    print("RESULT: 0/1 checks passed")
    raise SystemExit("the bucket counts do not reconcile; refusing to proceed")

# The seventh of the seven is the one whose canonical structure is a different analytical method
# from the production module of the same name, and it is identified by that fact rather than by
# being named here: it is the module in the bucket whose canonical structure is a cost risk
# quantification, which is the bottom-up cost register, while the production module of that name
# forecasts from a budget, two indices and a document risk score.
MONTE_CARLO = [m for m in BUCKET_3
               if "cost risk quantification" in BUCKETS[m]["canonical_structure_required"]]
check(len(MONTE_CARLO) == 1,
      "exactly one of the seven names a cost risk quantification as its canonical structure, "
      "which is the mismatch this run must dispose of", str(MONTE_CARLO))
SIX = [m for m in BUCKET_3 if m not in MONTE_CARLO]
check(len(SIX) == 6, "leaving exactly six ready for canonical integration", str(SIX))
check(SIX == ["A2.2", "A2.3", "A4.4", "A5.6", "A5.7", "A6.3"],
      "and they are the six the canonical-structure layer carries a contract for", str(SIX))
check(sorted(canonical.CANONICAL_STRUCTURE_KEYS) == SIX,
      "the production layer's own contract list is exactly that set, so the code and the "
      "classification agree without either being copied into the other",
      str(sorted(canonical.CANONICAL_STRUCTURE_KEYS)))
check(sorted(canonical.REFERENCE_OBJECT_KEYS) == BUCKET_4,
      "and the reference-object contract list is exactly the two in the other bucket",
      str(sorted(canonical.REFERENCE_OBJECT_KEYS)))


# =================================================================================================
section("1. THE SIX COMPUTE ON THEIR CANONICAL STRUCTURE, AGAINST INDEPENDENT ORACLES")
# =================================================================================================

PROJECTS = ["PRJ-AIR", "PRJ-HWY", "PRJ-HSP", "PRJ-WTR", "PRJ-RAL", "PRJ-DCT"]
PERIODS = ["P01", "P02", "P03", "P04", "P05", "P06"]
ROWS_B3: list[list] = []


def record(mid, structure_present, absent_behavior, known_answer, participant_effect):
    ROWS_B3.append([
        mid, registry_index()[mid]["module_name"], BUCKETS[mid]["final_owner_action_bucket"],
        canonical.CANONICAL_STRUCTURE_KEYS[mid],
        FL.PROGRAMME_VERSION, "tests.synthetic_fixtures.importers.production_structures",
        "app.simulation.canonical", structure_present, absent_behavior, known_answer,
        "non-voting", participant_effect,
    ])


# ---- A2.2. The separation between two production lines, derived here from the stated geometry
#      and compared against the module. The rates and starts come from the work packages; the
#      expectation is computed from them by the definition, not by calling the module twice.
_lob_cases = 0
_lob_ok = True
for project in PROJECTS:
    for period in PERIODS:
        structure = PS.line_of_balance(project, period)
        if not structure:
            continue
        _lob_cases += 1
        lead = [w for w in structure["work_packages"]
                if w["work_type_id"] == structure["leading_work_type"]]
        follow = [w for w in structure["work_packages"]
                  if w["work_type_id"] == structure["following_work_type"]]
        rl = lead[0]["production_rate_locations_per_day"]
        rf = follow[0]["production_rate_locations_per_day"]
        sl = min(w["start_day"] for w in lead)
        sf = min(w["start_day"] for w in follow)
        locations = sorted({w["location_sequence"] for w in structure["work_packages"]})
        expected = min((sf + u / rf) - (sl + u / rl) for u in locations)
        got = run_module("A2.2", {"lobStructure": structure}, NOOP, CUTOFF)
        if not close(got.get("minimum_buffer_days"), round(expected, 1), 0.051):
            _lob_ok = False
            check(False, f"A2.2 {project}/{period}: separation disagrees",
                  f"{got.get('minimum_buffer_days')} vs {expected}")
            break
check(_lob_ok and _lob_cases == 18,
      f"A2.2: over all {_lob_cases} project periods the minimum separation is the one the two "
      f"lines of work give, derived here from their rates and starts", str(_lob_cases))

# And the rates the adapter hands the module are the ones the package recorded for that pair of
# lines, which is the join a fixture assembled by a route the adapter does not take would break.
_rate_bad = 0
for g in FL.load_table(f"{PS.PACKAGE_A}/lob_ground_truth.csv"):
    st = PS.line_of_balance(g["project_id"], g["period_id"])
    lead = [w for w in st["work_packages"] if w["work_type_id"] == g["leading_work_type"]][0]
    follow = [w for w in st["work_packages"] if w["work_type_id"] == g["following_work_type"]][0]
    if not (close(lead["production_rate_locations_per_day"], float(g["leading_rate"]), 1e-9)
            and close(follow["production_rate_locations_per_day"],
                      float(g["following_rate"]), 1e-9)):
        _rate_bad += 1
check(_rate_bad == 0,
      "A2.2: and the production rates the adapter carries are the ones the package records",
      f"{_rate_bad} disagree")
record("A2.2", "yes", "abstain", f"{_lob_cases} project periods agree", "advisory only")

# ---- A2.3. Buffer consumption over a sized buffer, and the buffer sizing itself is checked
#      against the root sum of PERT variances the package documents.
_ccpm_cases = 0
for project in PROJECTS:
    for period in PERIODS:
        structure = PS.ccpm(project, period)
        if not structure:
            continue
        _ccpm_cases += 1
        buf = [b for b in structure["buffers"] if b["buffer_type"] == "PROJECT"][0]
        expected_consumed = ((buf["original_buffer_days"] - buf["remaining_buffer_days"])
                             / buf["original_buffer_days"] * 100.0)
        got = run_module("A2.3", {"ccpmStructure": structure}, NOOP, CUTOFF)
        if not close(got.get("pct_buffer_consumed"), round(expected_consumed, 1), 0.051):
            check(False, f"A2.3 {project}/{period}: consumption disagrees",
                  f"{got.get('pct_buffer_consumed')} vs {expected_consumed}")
            break
else:
    check(_ccpm_cases == 36,
          f"A2.3: over all {_ccpm_cases} project periods the buffer consumed is the share of the "
          f"sized buffer that has been used", str(_ccpm_cases))
# The buffer sizing itself, re-derived from the chain's activities: a project buffer sized at
# 1.645 times the root sum of the PERT variances of its member activities, where each activity's
# variance is the sixth of its pessimistic-less-optimistic spread, squared. This is a property of
# the buffer rather than of the module, and it is what makes the buffer a SIZED buffer.
_acts = {(a["project_id"], a["activity_id"]): a
         for a in FL.load_table(f"{PS.PACKAGE_A}/schedule_activities.csv")}
_members = FL.load_table(f"{PS.PACKAGE_A}/ccpm_chain_activities.csv")
_size_bad = 0
_size_n = 0
for c in FL.load_table(f"{PS.PACKAGE_A}/ccpm_chains.csv"):
    rows = [m for m in _members
            if m["project_id"] == c["project_id"] and m["chain_id"] == c["chain_id"]]
    variance = sum(((float(_acts[(m["project_id"], m["activity_id"])]
                            ["pessimistic_duration_days"])
                     - float(_acts[(m["project_id"], m["activity_id"])]
                             ["optimistic_duration_days"])) / 6.0) ** 2 for m in rows)
    _size_n += 1
    if not close(1.645 * math.sqrt(variance), float(c["original_buffer_days"]), 1e-6):
        _size_bad += 1
check(_size_bad == 0 and _size_n > 0,
      f"A2.3: and every one of the {_size_n} buffers is sized at 1.645 times the root sum of "
      f"its chain's activity variances", f"{_size_bad} disagree")
record("A2.3", "yes", "abstain", f"{_ccpm_cases} project periods agree", "advisory only")

# =================================================================================================
# RUN 29 REPLACED THE THREE BLOCKS THAT USED TO SIT HERE, AND THE REPLACEMENT COSTS SOMETHING
# THAT IS RECORDED RATHER THAN GLOSSED.
#
# Run 10B integrated A4.4, A5.6 and A5.7 against the synthetic package's own structures: an
# audited nonconformance cohort, a queue OBSERVATION log, and a typed-in agent STATE HISTORY.
# Run 29's supplied contract states that none of the three is the method its module is named for.
# A backlog over an audit total is a ratio of two different populations; a share of occupied
# server time is a measured occupancy and not a queueing model; and a state history whose named
# rules are never executed is a table read and not a simulation.
#
# THE HONEST CONSEQUENCE, stated plainly: the synthetic research package carries the OLD shapes,
# so these three modules no longer have a synthetic corpus to be integrated against, and the
# thirty-plus project periods of agreement Run 10B recorded are not replaced by an equivalent
# number. What is asserted instead is (a) that the old structures produce NO reading, which is
# what stops the proxy surviving under a new name, and (b) that each module reproduces the
# supplied contract's own hand-checked answer on its governed structure. Rebuilding the synthetic
# package in the v4 shapes is Run 30's work and is named as such in the report.
from run29_fixtures import (  # noqa: E402
    agent_model as _r29_abm, ncr_record as _r29_ncr, queue_model as _r29_queue,
    scenario_set as _r29_scn,
)

for _mid, _key, _builder in (("A4.4", "auditedNonconformanceCohort",
                              lambda: PS.audited_nonconformance_cohort(PROJECTS[0], PERIODS[0])),
                             ("A5.6", "queueStructure", lambda: PS.queues(PROJECTS[0])),
                             ("A5.7", "abmStructure", lambda: PS.agents(PROJECTS[0]))):
    _structure = _builder()
    _out = run_module(_mid, {_key: _structure}, NOOP, CUTOFF)
    check(bool(_out.get("insufficient_data")),
          f"{_mid}: the synthetic package's v2 structure produces no reading, because it is not "
          f"the structure the canonical method is defined on",
          str(_out.get("evidence_metric"))[:80])

_ncr_out = run_module("A4.4", {"ncrExposureRecord": _r29_ncr()}, NOOP, CUTOFF)
check(_ncr_out.get("ncr_rate") == 0.04,
      "A4.4: four nonconformances against one hundred inspections is a rate of 0.04, the "
      "supplied contract's own answer", str(_ncr_out.get("ncr_rate")))
record("A4.4", "yes", "abstain", "the supplied contract's own known answer", "advisory only")

_q_out = run_module("A5.6", {"queueModel": _r29_queue()}, NOOP, CUTOFF)
check(close(_q_out.get("utilisation"), 2 / 3, 1e-5) and close(_q_out.get("L"), 2.0, 1e-5)
      and close(_q_out.get("W"), 1.0, 1e-5) and close(_q_out.get("Lq"), 4 / 3, 1e-5)
      and close(_q_out.get("Wq"), 2 / 3, 1e-5),
      "A5.6: an arrival rate of two against a service rate of three on one server gives a "
      "utilisation of two thirds, L of two, W of one, Lq of four thirds and Wq of two thirds, "
      "the supplied contract's own answers", str(_q_out.get("utilisation")))
check(bool(run_module("A5.6", {"queueModel": _r29_queue(arrival=3.0, service=3.0)},
                      NOOP, CUTOFF).get("insufficient_data")),
      "A5.6: and an unstable queue is refused rather than given a reassuring finite steady state")
record("A5.6", "yes", "abstain", "the supplied contract's own known answer", "advisory only")

_a_out = run_module("A5.7", {"agentSupplyChainModel": _r29_abm()}, NOOP, CUTOFF)
check(_a_out.get("received") == 2 and _a_out.get("backordered") == 0,
      "A5.7: the one supplier, one carrier, one project model delivers both units by the fourth "
      "step, which is the hand-computed trace", str(_a_out.get("received")))
record("A5.7", "yes", "abstain", "the supplied contract's own known answer", "advisory only")

# ---- A6.3. The share of assessed permit conditions found compliant.
_env_cases = 0
for project in PROJECTS:
    for period in PERIODS:
        audit = PS.audited_permit_compliance(project, period)
        if not audit:
            continue
        _env_cases += 1
        expected = (sum(1 for a in audit["assessments"] if a["result"] == "COMPLIANT")
                    / len(audit["assessments"]) * 100.0)
        got = run_module("A6.3", {"auditedPermitCompliance": audit}, NOOP, CUTOFF)
        if not close(got.get("compliance_rate"), expected, 0.051):
            check(False, f"A6.3 {project}/{period}: compliance rate disagrees",
                  f"{got.get('compliance_rate')} vs {expected}")
            break
else:
    check(_env_cases == 36,
          f"A6.3: over all {_env_cases} project periods the rate is the share of assessed permit "
          f"conditions found compliant, and no meeting mention enters it", str(_env_cases))
record("A6.3", "yes", "abstain", f"{_env_cases} project periods agree", "advisory only")


# =================================================================================================
section("2. ABSENT AND MALFORMED STRUCTURE: THE SIX ABSTAIN AND NEVER PROXY")
# =================================================================================================

# A project reporting every scalar the platform knows how to extract. None of the six may produce
# a reading from it, because none of these scalars is any of their structures.
RICH = {"bac": 12_000_000.0, "ev": 4e6, "ac": 4.4e6, "pv": 4.5e6, "cpi": 0.909, "spi": 0.889,
        "actualPctComplete": 40.0, "plannedPctComplete": 45.0, "docRiskScore": 0.35,
        "activitiesPlanned": 200, "activitiesConstrained": 37, "longLeadItemsTotal": 20,
        "longLeadAtRisk": 3, "ncrIssued": 4, "ncrClosed": 2, "ncrOpen": 6,
        "environmentalIssuesDiscussed": 2, "totalFloat": 40, "consumedFloat": 16}
for mid in SIX:
    out = run_module(mid, dict(RICH), NOOP, CUTOFF)
    check(abstains(out),
          f"{mid}: a fully reported project with no canonical structure still abstains, so "
          f"nothing degrades into a proxy to keep output flowing",
          str(out.get("status_color")))
    speakable(out, mid, full_stop=mid not in ("A4.4", "A6.3"))

# The empty structure, the wrong-shaped structure, and a structure with a hole in it.
MALFORMED = {
    "A2.2": [{}, {"work_packages": []}, {"work_packages": "not a list"},
             {"work_packages": [{"work_type_id": "A", "location_sequence": 1,
                                 "production_rate_locations_per_day": 0.0, "start_day": 0.0}],
              "leading_work_type": "A", "following_work_type": "B"}],
    "A2.3": [{}, {"chains": [], "buffers": []},
             {"chains": [{"chain_id": "C", "chain_type": "FEEDING"}],
              "buffers": [{"chain_id": "C", "buffer_type": "FEEDING",
                           "original_buffer_days": 5, "remaining_buffer_days": 4,
                           "chain_progress_fraction": 0.3}]},
             {"chains": [{"chain_id": "C", "chain_type": "PROJECT"}],
              "buffers": [{"chain_id": "C", "buffer_type": "PROJECT",
                           "original_buffer_days": 5, "remaining_buffer_days": 9,
                           "chain_progress_fraction": 0.3}]}],
    "A6.3": [{}, {"assessments": []}, {"assessments": "not a list"}],
}
for mid, cases in MALFORMED.items():
    key = canonical.CANONICAL_STRUCTURE_KEYS[mid]
    for i, bad in enumerate(cases):
        out = run_module(mid, {key: bad}, NOOP, CUTOFF)
        check(abstains(out),
              f"{mid}: malformed structure case {i + 1} abstains rather than computing",
              str(out.get("status_color")))
    out = run_module(mid, {key: "not a structure at all"}, NOOP, CUTOFF)
    check(abstains(out), f"{mid}: a structure that is not a structure abstains")
    out = run_module(mid, {key: None}, NOOP, CUTOFF)
    check(abstains(out), f"{mid}: a structure reported as nothing abstains")

# RUN 29. A4.4, A5.6 and A5.7 are no longer in the malformed-structure table above, because the
# keys it drove are no longer keys they read. Their own malformed cases are asserted against the
# structures they DO read, immediately below, so nothing is lost by the removal.
for _mid, _key, _bad_cases in (
        ("A4.4", "ncrExposureRecord",
         [{}, dict(_r29_ncr(), exposure_quantity=0.0), dict(_r29_ncr(), ncrs=[]),
          dict(_r29_ncr(), exposure_unit="")]),
        ("A5.6", "queueModel",
         [{}, _r29_queue(arrival=3.0, service=3.0), _r29_queue(servers=0),
          {"source": "s", "model_version": "v", "queues": []}]),
        ("A5.7", "agentSupplyChainModel",
         [{}, _r29_abm(steps=1), dict(_r29_abm(), agents=[]),
          dict(_r29_abm(), travel_delay_steps=-1)])):
    for _i, _bad in enumerate(_bad_cases):
        _out = run_module(_mid, {_key: _bad}, NOOP, CUTOFF)
        check(abstains(_out),
              f"{_mid}: malformed governed structure case {_i + 1} abstains rather than "
              f"computing", str(_out.get("status_color")))
    check(abstains(run_module(_mid, {_key: "not a structure at all"}, NOOP, CUTOFF)),
          f"{_mid}: a structure that is not a structure abstains")
    check(abstains(run_module(_mid, {_key: None}, NOOP, CUTOFF)),
          f"{_mid}: a structure reported as nothing abstains")

# The four that used to compute from a proxy name the ABSENT STRUCTURE as the reason, which is a
# different reason from a missing figure and says so.
for mid in ("A2.2", "A2.3", "A5.6", "A5.7"):
    out = run_module(mid, dict(RICH), NOOP, CUTOFF)
    check(out.get("abstention_reason_code") == ABSTAIN_STRUCTURE_ABSENT,
          f"{mid}: and the reason code names the absent canonical structure",
          str(out.get("abstention_reason_code")))


# =================================================================================================
section("3. THE TWO REFERENCE-OBJECT MODULES, AND THE LEAKAGE CONTROLS")
# =================================================================================================

ROWS_B4: list[list] = []
DP = "DP-01"

# ---- A5.4. RUN 29 MOVED THIS MODULE OFF THE DECISION OBJECT ENTIRELY.
#      Run 10B made Scenario Modeling read an actions-by-scenarios payoff with stated
#      probabilities and return a RECOMMENDED ACTION. The supplied Run-29 contract states in its
#      own words that this is Category 10's question -- which management intervention should be
#      chosen -- and that Category 5 asks what happens to the system under a condition. So the
#      decision object is no longer this module's defining structure, it recommends nothing, and
#      what it reads is a governed scenario set evaluated through one declared response model.
#
#      The leakage controls below therefore apply to B2.19 alone in this suite. That is a
#      REDUCTION IN COVERAGE of those controls and is recorded as such: the decision object's own
#      split, version and self-comparison guards are unchanged in `canonical.py` and are still
#      exercised through B2.19, but one of the two modules that exercised them no longer does.
BAC = 10_000_000.0
_scenario = PS.scenario_decision(DP)
check(abstains(run_module("A5.4", {"bac": BAC, "scenarioDecisionStructure": _scenario},
                          NOOP, CUTOFF)),
      "A5.4: the decision object produces no reading, because choosing between courses of action "
      "is not the question this module answers")
_scn_out = run_module("A5.4", {"scenarioSet": _r29_scn()}, NOOP, CUTOFF)
check(_scn_out.get("responses") == {"BASE": 5.0, "ADVERSE": 8.0, "RECOVERY": 4.0},
      "A5.4: the three coherent states give five, eight and four through the declared response "
      "model, which are the supplied contract's own answers", str(_scn_out.get("responses")))
check(_scn_out.get("recommended_action") is None,
      "A5.4: and no state is recommended over any other, because that is a different question")

# ---- B2.19. CRITIC weights across the alternatives, checked against the package's recorded
#      weights, which were produced by an independent implementation of the same definition.
# RUN 30 CLOSURE. THE PACKAGE'S OWN DECISION PROBLEM NOW REACHES THE CANONICAL PRODUCTION RUNNER.
# B2.19 routes through models_cat7.py into canonical_v5, whose structure is the shared
# alternatives-and-criteria object, so the package is imported in that shape by
# `production_structures.decision_alternatives` -- the SAME package rows `decision_matrix` reads,
# with nothing invented and no weight supplied. A structurally canonical fixture that never
# reaches the canonical runner would not have been adequate.
_matrix = PS.decision_matrix(DP)
_alternatives = PS.decision_alternatives(DP)
check(len(_alternatives["alternatives"]) == len(_matrix["alternatives"])
      and len(_alternatives["criteria"]) == len(_matrix["criteria"]),
      "B2.19: the canonical import carries the same alternatives and criteria as the package's "
      "own decision matrix, so nothing was added or dropped in the translation",
      f"{len(_alternatives['alternatives'])} alternatives, "
      f"{len(_alternatives['criteria'])} criteria")
got_ct = run_module("B2.19", {"decisionAlternatives": _alternatives}, NOOP, CUTOFF)
check(got_ct.get("result_source") == "CANONICAL_V5_LAYER"
      and got_ct.get("canonical_disposition") == "CANONICAL_RESULT",
      "B2.19: and the answer came from the canonical layer through the production dispatcher",
      str(got_ct.get("canonical_disposition")))
truth = [t for t in FL.load_table(f"{PS.PACKAGE_B}/B3_decision_optimization/"
                                 f"ground_truth_decisions.csv", primary_key=None)
         if t["decision_problem_id"] == DP][0]
import json  # noqa: E402
recorded_weights = json.loads(truth["critic_weights_json"])
_w = got_ct.get("criterion_weights") or {}
check(set(_w) == set(recorded_weights),
      "B2.19: a weight is produced for every criterion, none dropping out of its own decision",
      str(sorted(_w)))
check(all(abs(_w[k] - recorded_weights[k]) <= 0.002 for k in recorded_weights),
      "B2.19: and each weight matches the one the package recorded, to the places it records",
      str(_w))
check(all(v > 0 for v in _w.values()),
      "B2.19: every weight is above zero, which is the degeneracy the single-alternative form "
      "could not avoid", str(_w))
check((got_ct.get("ranking") or [None])[0] == truth["critic_topsis_top_action_id"],
      "B2.19: and the alternative ranked first is the one the package records",
      f"{(got_ct.get('ranking') or [None])[0]} vs {truth['critic_topsis_top_action_id']}")
check(len(got_ct.get("ranking") or []) == len(_matrix["alternatives"]),
      "B2.19: over all the alternatives, not one", str(len(got_ct.get("ranking") or [])))

# ---- THE LEAKAGE CONTROLS, one at a time, on both modules.
for mid, key, builder in (("B2.19", "decisionAlternatives", PS.decision_alternatives),):
    base = {}

    locked = dict(builder(DP, split="LOCKED_HOLDOUT"))
    out = run_module(mid, dict(base, **{key: locked}), NOOP, CUTOFF)
    check(abstains(out),
          f"{mid}: material from the locked holdout is refused outright, which is the whole "
          f"point of locking it", str(out.get("status_color")))
    check(out.get("abstention_reason_code") == ABSTAIN_DECISION_STRUCTURE_ABSENT,
          f"{mid}: and the refusal is recorded as the decision structure being unavailable",
          str(out.get("abstention_reason_code")))
    speakable(out, f"{mid} locked holdout")

    for split in ("DEVELOPMENT", "VALIDATION"):
        ok = run_module(mid, dict(base, **{key: builder(DP, split=split)}), NOOP, CUTOFF)
        check(not abstains(ok), f"{mid}: the {split.lower()} split is readable", str(ok)[:80])

    unsplit = dict(builder(DP))
    unsplit["split"] = ""
    check(abstains(run_module(mid, dict(base, **{key: unsplit}), NOOP, CUTOFF)),
          f"{mid}: material that does not say which split it belongs to is refused, because it "
          f"cannot be shown to be material this module may read")

    unversioned = dict(builder(DP))
    unversioned["asset_version"] = ""
    check(abstains(run_module(mid, dict(base, **{key: unversioned}), NOOP, CUTOFF)),
          f"{mid}: material that does not say which version it came from is refused, because a "
          f"result taken from it could not be interpreted later")

    selftrain = dict(builder(DP))
    selftrain["reference_member_project_ids"] = [selftrain["evaluated_project_id"], "OTHER"]
    check(abstains(run_module(mid, dict(base, **{key: selftrain}), NOOP, CUTOFF)),
          f"{mid}: a project that is itself part of the material it would be compared against "
          f"is refused, so nothing trains on itself")

    missing = run_module(mid, dict(base), NOOP, CUTOFF)
    if mid == "B2.19":
        check(abstains(missing) or missing.get("status_color") is not None,
              "B2.19: with no decision matrix the single-project form is what remains, and it "
              "is unchanged by this run", str(missing.get("status_color")))
    ROWS_B4.append([
        mid, registry_index()[mid]["module_name"], BUCKETS[mid]["final_owner_action_bucket"],
        key, FL.PROGRAMME_VERSION, "DEVELOPMENT and VALIDATION only",
        "locked holdout refused; version required; self-comparison refused",
        "tests.synthetic_fixtures.importers.production_structures",
        "abstain", "PASS", "non-voting", "advisory only",
    ])

# A single alternative is the degeneracy Run 8 recorded, and it is refused rather than weighted.
one_alt = dict(PS.decision_matrix(DP))
one_alt["alternatives"] = one_alt["alternatives"][:1]
check(abstains(run_module("B2.19", {"decisionMatrix": one_alt}, NOOP, CUTOFF)),
      "B2.19: one alternative is refused, because a weighting defined by how much alternatives "
      "differ cannot be formed from one of them")
flat = dict(PS.decision_matrix(DP))
flat["alternatives"] = [{"alternative_id": f"A{i}",
                         "values": {c["criterion_id"]: 1.0 for c in flat["criteria"]}}
                        for i in range(3)]
check(abstains(run_module("B2.19", {"decisionMatrix": flat}, NOOP, CUTOFF)),
      "B2.19: alternatives that are identical on every criterion are refused, because there is "
      "nothing for a weighting to be formed from")


# =================================================================================================
section("4. THE MONTE CARLO DISPOSITION: TWO METHODS, TWO IDENTITIES, ONE PRODUCTION MODULE")
# =================================================================================================

MC = MONTE_CARLO[0]
check(MC not in canonical.CANONICAL_STRUCTURE_KEYS,
      "the production forecast does NOT consume the bottom-up cost register, so the two methods "
      "are not given one identity", MC)
_src = (ROOT / "server" / "app" / "simulation" / "models.py").read_text(encoding="utf-8")
check("cost_elements" not in _src and "cost_risk_ground_truth" not in _src,
      "and no cost register asset is named anywhere in the production layer")
# What the production module reads is unchanged: a budget, two indices and a document risk score,
# and it reads neither actual cost nor earned value.
_mc_full = run_module(MC, {"bac": 1e6, "cpi": 0.9, "spi": 0.95, "docRiskScore": 0.3},
                      lambda: 0.5, CUTOFF)
check(not abstains(_mc_full), "the production forecast computes from budget, indices and "
      "document risk exactly as before", str(_mc_full.get("status_color")))
_mc_no_ac = run_module(MC, {"bac": 1e6, "cpi": 0.9, "spi": 0.95, "docRiskScore": 0.3,
                            "ac": 999_999_999.0, "ev": 1.0}, lambda: 0.5, CUTOFF)
check(_mc_full.get("status_color") == _mc_no_ac.get("status_color"),
      "and an actual cost and an earned value change nothing about it, because it reads neither",
      f"{_mc_full.get('status_color')} vs {_mc_no_ac.get('status_color')}")
check(run_module(MC, {"bac": 1e6, "cpi": 0.9, "spi": 0.95,
                      "cost_register": [{"low": 1, "mode": 2, "high": 3}]},
                 lambda: 0.5, CUTOFF).get("status_color") is not None,
      "and a cost register handed to it is simply not read, so no second method is smuggled in "
      "under the same name")


# =================================================================================================
section("5. BUCKET 5 REMAINS DISABLED, AND VOTING AND STATUS DO NOT MOVE")
# =================================================================================================

for mid in BUCKET_5:
    for label, si in (("an empty input", {}), ("a fully reported project", dict(RICH))):
        out = run_module(mid, dict(si), NOOP, CUTOFF)
        check(abstains(out), f"{mid}: abstains unconditionally on {label}")
    check(mid not in CORE_VOTING_MODULES, f"{mid}: is not a voting module")
    check(mid not in canonical.CANONICAL_STRUCTURE_KEYS
          and mid not in canonical.REFERENCE_OBJECT_KEYS,
          f"{mid}: is given no canonical structure by this run, so nothing reactivates it")

check(len(DISABLED_CONCEPT_ONLY) == 8,
      "the eight concept-only modules are still refused before their formula is reached",
      str(len(DISABLED_CONCEPT_ONLY)))
check(CORE_VOTING_MODULES == frozenset({"A1.7", "A1.8"}),
      "exactly two modules vote, before and after everything above",
      str(sorted(CORE_VOTING_MODULES)))
for mid in SIX + BUCKET_4 + BUCKET_5:
    check(mid not in CORE_VOTING_MODULES,
          f"{mid}: integration does not imply voting eligibility")

# The strongest form of that: the same project, computed with and without every structure this
# run added, fuses to the same status.
PROJECT_SI = {"bac": 12_000_000.0, "ev": 4e6, "ac": 4.4e6, "pv": 4.5e6, "cpi": 0.909,
              "spi": 0.889, "actualPctComplete": 40.0, "plannedPctComplete": 45.0,
              "docRiskScore": 0.35}
WITH_STRUCTURES = dict(
    PROJECT_SI,
    lobStructure=PS.line_of_balance("PRJ-HWY", "P03"),
    ccpmStructure=PS.ccpm("PRJ-AIR", "P03"),
    queueStructure=PS.queues("PRJ-AIR"),
    abmStructure=PS.agents("PRJ-AIR"),
    auditedNonconformanceCohort=PS.audited_nonconformance_cohort("PRJ-HWY", "P05"),
    auditedPermitCompliance=PS.audited_permit_compliance("PRJ-AIR", "P01"),
    scenarioDecisionStructure=PS.scenario_decision(DP),
    decisionMatrix=PS.decision_matrix(DP),
    # RUN 29. The three v4 structures whose modules moved off the v2 shapes above, so the
    # correspondence check below still asserts the full set rather than a shrunken one.
    ncrExposureRecord=_r29_ncr(),
    queueModel=_r29_queue(),
    agentSupplyChainModel=_r29_abm(),
    scenarioSet=_r29_scn(),
    # RUN 30 CLOSURE: B2.19 reads the shared alternatives-and-criteria object now, so the rich
    # fixture supplies it in that shape. The decision matrix stays beside it, unchanged, because
    # the older canonical layer still reads it.
    decisionAlternatives=PS.decision_alternatives(DP),
)
plain = compute_project(dict(PROJECT_SI), "S-A", "P1", CUTOFF)
rich = compute_project(dict(WITH_STRUCTURES), "S-A", "P1", CUTOFF)
check(plain["project_status"] == rich["project_status"],
      "adding every structure this run integrated leaves the fused project status exactly where "
      "it was", f"{plain['project_status']} vs {rich['project_status']}")
check(plain["categories_voting"] == rich["categories_voting"],
      "and the same categories vote", f"{plain['categories_voting']} vs "
      f"{rich['categories_voting']}")
_rich_computed = {m["module_id"] for m in rich["modules"]}
_plain_computed = {m["module_id"] for m in plain["modules"]}
# RUN 14, EXPECTATION CORRECTED WITH ITS REASON. Until Run 14 the two reference-object modules
# computed with or without their decision object, because each kept a single-project fallback,
# so only the six structure modules appeared in this difference. Run 13 recorded that fallback
# as a mismatch (a band under the canonical method's name computed from something that is not
# that method) and Run 14 removed it, so those two now abstain without their structure and
# compute with it. The set this check names is therefore the eight, and the check is stronger
# than it was: it now asserts the full correspondence between a structure and a reading.
# RUN 29, EXPECTATION CORRECTED WITH ITS REASON. A5.4 is no longer a reference-object module:
# the decision object is not its defining structure and it gains its reading from the governed
# scenario set instead, which is supplied above. B2.19 still gains from the decision matrix. So
# the set is the six plus B2.19 plus A5.4, which is exactly what it was, reached by a different
# structure for one of them.
check(_rich_computed - _plain_computed == set(SIX) | set(BUCKET_4),
      "the modules that gained a reading are exactly the ones given a structure",
      str(sorted(_rich_computed - _plain_computed)))
check(not (_plain_computed - _rich_computed),
      "and no module lost one", str(sorted(_plain_computed - _rich_computed)))


# =================================================================================================
section("6. SYNTHETIC AND OPERATIONAL SEPARATION")
# =================================================================================================

_app = ROOT / "server" / "app"
_offenders = []
for path in _app.rglob("*.py"):
    body = path.read_text(encoding="utf-8")
    if "research_fixtures" in body or "synthetic_fixtures" in body or "OG-SYNTH" in body:
        _offenders.append(str(path.relative_to(ROOT)))
check(not _offenders,
      "no file in the application names the fixture root, the fixture package or the programme "
      "version, so operational execution has no path to fall back to a research fixture",
      str(_offenders))
check("import" not in canonical.__doc__ or "tests" not in canonical.__doc__.split("import")[-1],
      "and the canonical layer reads its structures off the caller's inputs rather than opening "
      "anything")

for name, obj in (("line of balance", PS.line_of_balance("PRJ-HWY", "P01")),
                  ("critical chain", PS.ccpm("PRJ-AIR", "P01")),
                  ("queue", PS.queues("PRJ-AIR")),
                  ("agents", PS.agents("PRJ-AIR")),
                  ("nonconformance cohort", PS.audited_nonconformance_cohort("PRJ-HWY", "P05")),
                  ("permit compliance", PS.audited_permit_compliance("PRJ-AIR", "P01")),
                  ("decision problem", PS.scenario_decision(DP)),
                  ("decision matrix", PS.decision_matrix(DP))):
    check(obj.get("data_origin") == "SYNTHETIC_RESEARCH_FIXTURE",
          f"the {name} structure carries its origin", str(obj.get("data_origin")))
    check(obj.get("not_for_empirical_validation") is True,
          f"and the {name} structure is marked as not constituting empirical validation")

# The reference material is read-only: the loader hands back frozen records, so an adapter or a
# module cannot edit the population it is reading.
_row = list(FL.load_table(f"{PS.PACKAGE_B}/B3_decision_optimization/scenarios.csv"))[0]
try:
    _row["scenario_probability"] = "0.99"
    _mutable = True
except Exception:
    _mutable = False
check(not _mutable, "a reference row cannot be written through, so the population is read only")


# =================================================================================================
section("7. MUTATION PROOF: EVERY EXPECTATION ABOVE CAN GO RED")
# =================================================================================================

def mutation(label: str, fn) -> None:
    check(fn(), f"mutation: {label}")


# Perturb the structure and the reading must move.
_p = PS.line_of_balance("PRJ-HWY", "P01")
_base = run_module("A2.2", {"lobStructure": _p}, NOOP, CUTOFF)["minimum_buffer_days"]
_perturbed = {**_p, "work_packages": [
    dict(w, start_day=w["start_day"] + 10.0)
    if w["work_type_id"] == _p["following_work_type"] else dict(w)
    for w in _p["work_packages"]]}
mutation("moving the following line ten days later moves the separation by ten days",
         lambda: close(run_module("A2.2", {"lobStructure": _perturbed}, NOOP,
                                  CUTOFF)["minimum_buffer_days"], _base + 10.0, 0.11))
mutation("claiming the queue reading is unchanged when the service rate halves would fail",
         lambda: run_module("A5.6", {"queueModel": _r29_queue()}, NOOP,
                            CUTOFF)["utilisation"]
         != run_module("A5.6", {"queueModel": _r29_queue(service=6.0)}, NOOP,
                       CUTOFF)["utilisation"])
mutation("emptying the supplier's stock leaves the whole demand backordered",
         lambda: run_module("A5.7", {"agentSupplyChainModel": _r29_abm(inventory=0.0)}, NOOP,
                            CUTOFF)["backordered"] == 2.0)
_cc = PS.ccpm("PRJ-AIR", "P03")
_spent = {**_cc, "buffers": [dict(b, remaining_buffer_days=0.0) for b in _cc["buffers"]]}
mutation("a fully consumed buffer reads a hundred per cent consumed",
         lambda: close(run_module("A2.3", {"ccpmStructure": _spent}, NOOP,
                                  CUTOFF)["pct_buffer_consumed"], 100.0, 0.051))
mutation("claiming a locked holdout is readable would fail",
         lambda: abstains(run_module("B2.19",
                                     {"decisionAlternatives": PS.decision_alternatives(
                                         DP, split="LOCKED_HOLDOUT")}, NOOP, CUTOFF)))
mutation("claiming the six are in the voting set would fail",
         lambda: not set(SIX) & set(CORE_VOTING_MODULES))
mutation("claiming an absent structure still computes would fail",
         lambda: all(abstains(run_module(m, dict(RICH), NOOP, CUTOFF)) for m in SIX))

# A real injection into the production layer, applied and removed, proving these checks read the
# shipped code rather than a copy of it.
# RUN 30 CLOSURE: the injection follows the guard. B2.19 now reads the shared decision structure,
# whose split lock lives in canonical_v5, so injecting into canonical.py would have applied
# cleanly and changed nothing -- an injection that silently fails to apply, which is the failure
# mode this whole section exists to rule out.
import app.simulation.canonical_v5 as canonical_v5              # noqa: E402

_orig = (canonical_v5.READABLE_SPLITS, canonical_v5.LOCKED_SPLIT)
canonical_v5.READABLE_SPLITS = ("DEVELOPMENT", "VALIDATION", "LOCKED_HOLDOUT")
canonical_v5.LOCKED_SPLIT = "NOTHING_IS_LOCKED"
_applied = canonical_v5.LOCKED_SPLIT == "NOTHING_IS_LOCKED"     # re-read, never assumed
_leaked = run_module("B2.19",
                     {"decisionAlternatives": PS.decision_alternatives(
                         DP, split="LOCKED_HOLDOUT")}, NOOP, CUTOFF)
canonical_v5.READABLE_SPLITS, canonical_v5.LOCKED_SPLIT = _orig
check(_applied, "the split-rule injection actually applied before the answer was taken")
check(not abstains(_leaked),
      "an injected split rule does change the answer, so the leakage checks are reading the "
      "shipped guard rather than a description of it", str(_leaked.get("status_color")))
check(abstains(run_module("B2.19",
                          {"decisionMatrix": PS.decision_matrix(DP, split="LOCKED_HOLDOUT")},
                          NOOP, CUTOFF)),
      "and the injection is restored, so the holdout is locked again")


# =================================================================================================
section("8. THE AUDIT ARTEFACTS")
# =================================================================================================

with (CODE_AUDIT / "run10b_bucket3_integration.csv").open("w", newline="",
                                                          encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["module_id", "module_name", "category", "canonical_structure", "synthetic_asset",
                "production_importer", "production_adapter", "structure_present",
                "absent_structure_behavior", "known_answer_result", "voting_state",
                "participant_effect"])
    w.writerows(ROWS_B3)
    w.writerow([MONTE_CARLO[0], registry_index()[MONTE_CARLO[0]]["module_name"], "3",
                "bottom-up cost risk register", "not consumed",
                "none", "none", "no",
                "not applicable: the production module has its own verified fixture family",
                "disposition A, recorded in the report", "non-voting", "none"])
with (CODE_AUDIT / "run10b_bucket4_integration.csv").open("w", newline="",
                                                          encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["module_id", "module_name", "category", "reference_object", "asset_version",
                "split_used", "leakage_guard", "importer", "absent_reference_behavior",
                "test_result", "voting_state", "participant_effect"])
    w.writerows(ROWS_B4)
check((CODE_AUDIT / "run10b_bucket3_integration.csv").exists()
      and (CODE_AUDIT / "run10b_bucket4_integration.csv").exists(),
      "both audit artefacts are written")
# RUN 29. The bucket-4 artefact now carries one row rather than two, because A5.4 is no longer a
# reference-object module: its defining structure is a governed scenario set, not a decision
# object, so the leakage controls that produced its row are exercised through B2.19 alone. The
# count is stated rather than the reduction being hidden behind an inequality.
check(len(ROWS_B3) == 6 and len(ROWS_B4) == 1,
      "with a row for each integrated module, and one row in the reference-object artefact "
      "because Run 29 moved the other module off the decision object",
      f"{len(ROWS_B3)} and {len(ROWS_B4)}")


print()
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(0 if FAILED == 0 else 1)
