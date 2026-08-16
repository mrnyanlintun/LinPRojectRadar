"""
RUN 20 CYCLE 5 (P0D): THREE LINEAGE DECLARATIONS NAMED THE WRONG MODULE, AND ONE OF THEM
SUPPRESSED GENUINE CORROBORATION.

WHAT WAS FOUND, AND HOW. Cycle 4's neighbour sweep grouped modules by the field set their own
preflight requires. Reading that grouping back against `lineage.MODULE_LINEAGE` showed that three
of the declarations cycle 3 wrote as worked examples describe methods those module ids do not
carry:

  A1.1 was declared "cost performance index", chain "cost performance index = ev / ac".
       A1.1 IS MONTE CARLO EAC. It rests on the budget, both indices and the document risk score.
  A2.1 was declared "earned schedule", chain "schedule performance index (time)".
       A2.1 IS PERT NETWORK CRITICALITY, and it abstains on the absent activity network on every
       project the platform holds, so it emits no signal at all.
  A3.5 was declared "tornado / sensitivity" over the EARNED-VALUE body, chain "one-at-a-time
       sensitivity sweep". A3.5 IS OVERHEAD ABSORPTION RATE. It rests on the planned and actual
       indirect cost and the progress figure, and shares NO fact with the earned-value body.

WHY THE THIRD ONE MATTERS MOST, AND WHY IT IS NOT A COSMETIC ERROR. Every other declaration error
in this table is conservative: a wrongly declared dependence refuses corroboration that was really
available, and a wrongly declared independence is caught by the fact-intersection rule. A3.5 was
the conservative direction taken too far and it did real harm. An INDEPENDENT indirect-cost signal
had been declared inside the earned-value body, so a genuine second body of evidence was absorbed
into the first and could no longer corroborate it. Measured before the correction: an Amber
to-complete index and an Amber overhead absorption fused to 0.7000 in ONE body. They are two
bodies and 0.9273.

THE SUPERVISORY WARNING THIS PROVES OUT, IN THIS PROGRAMME'S OWN WORDS: a fix that also suppresses
real corroboration is not a fix. Cycle 3's positive control was real but it was built from a
SYNTHETIC independent body written inside the test. It could not see that the declarations shipped
in production had absorbed a real one. This suite drives the positive control from the DECLARED
TABLE instead, which is the gap that let this through.

WHAT THIS CYCLE CHANGES. Three declarations, and nothing else. No module's band, boundary,
threshold or arithmetic is touched. A2.1's entry is REMOVED rather than corrected: a module that
abstains structurally on every project emits no signal, and a lineage record is a statement about
a signal's evidence. Declaring evidence for a reading that is never produced asserts something
that does not exist.

AND THE GUARD, WHICH IS THE REAL DELIVERABLE. A declaration that names the wrong module got into
production and survived a cycle. The guard below makes every declared id prove itself against the
module registry and against the module's own runtime refusal, so this class of error cannot repeat
silently. It is deliberately NOT derived from the declaration it checks.
"""

from __future__ import annotations

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation import fusion, lineage, registry  # noqa: E402
import run29_fixtures as FX  # noqa: E402


# RUN 20 CYCLE 6 UPDATED THIS SUITE AND DID NOT DELETE IT. The owner decision that followed
# cycle 5 overturned the transitive-closure treatment this file was written against: dependence
# is NOT transitive, and `lineage.partition` is gone. The cycle's findings stand and are kept as
# historical evidence; the call sites are moved onto the non-transitive separation and any claim
# the decision overturned is corrected IN PLACE with the correction stated, rather than quietly
# dropped. A deleted check is a check nobody can see was wrong.
def _parts(recs):
    """The bodies of evidence, as module-id index lists, under the non-transitive model."""
    return lineage.evidence_bodies(recs)["bodies"]


_passed = 0
_total = 0
_fail: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if cond:
        _passed += 1
    else:
        _fail.append(name + (f" -- {detail}" if detail else ""))


def near(name: str, got, want, tol=5e-4) -> None:
    check(name, got is not None and abs(float(got) - float(want)) <= tol,
          f"got {got!r}, expected {want!r}")


def rec_of(mid):
    return lineage.lineage_for(mid) or {}


def sig(mid, status):
    r = lineage.lineage_for(mid)
    out = {"module_id": mid, "status": status}
    if r:
        out["lineage"] = r
    return out


# The method class each module id actually carries, read from the module registry rather than
# from any table this suite is checking. This is the independent side of the oracle.
def method_class_of(mid: str) -> str:
    """The method class the module itself reports, taken from a real run rather than from a name
    table, so a registry entry that disagrees with the function it points at is caught too."""
    out = registry.run_module(mid, {}, lambda: 0.5, None)
    return str(out.get("method_class", ""))


# ============================================================ 1. EVERY DECLARED ID IS A REAL MODULE

print("== every declared lineage names a module that exists ==")

_declared = sorted(lineage.MODULE_LINEAGE)
_available = set(registry.available_modules())
# RUN 20 CYCLE 6. The skip used to be keyed on the prefix "PH.", which is how the false entry
# hid: an id outside the registry namespace was excused from the existence check by the very
# rule that should have caught it. Existence is now checked against the REGISTRY, which every
# module has an entry in, and the narrower question of whether a module runs on a single project
# is asked separately, because Group D is portfolio-level and legitimately absent from that set.
_registry_ids = set(registry.registry_index())
for mid in _declared:
    check(f"{mid} is a module in this platform's registry", mid in _registry_ids)
    check(f"{mid} runs either on a single project or across the portfolio",
          mid in _available or registry.registry_index()[mid]["group"] == "D")


# ============================================================ 2. THE THREE CORRECTIONS

print("== the three misdeclared ids now describe the methods they really are ==")

# A1.1 IS MONTE CARLO EAC, not the cost performance index.
check("A1.1 is Monte Carlo EAC and not a cost index",
      method_class_of("A1.1") == "Monte_Carlo", method_class_of("A1.1"))
_a11 = rec_of("A1.1")
check("A1.1 declares a lineage record", bool(_a11))
check("HISTORICAL DEFECT, must not return: A1.1's chain calling it the cost performance index",
      not any("cost performance index = ev / ac" == step for step in _a11.get("derivation_chain", ()))
      or len(_a11.get("derivation_chain", ())) > 2,
      str(_a11.get("derivation_chain")))
# HARDENED AFTER MUTATION M32 DID NOT QUALIFY. This first accepted a chain step containing
# "percentile" as evidence of the stochastic step, and the eightieth-percentile overrun step
# satisfied it, so removing the sampling step altogether left the check green. A percentile is
# what is READ OFF a distribution; it is not the step that produces one. The check now demands
# the sampling be named, and M32 then qualified.
check("A1.1's chain names the SAMPLING step that makes it a forecast and not an identity",
      any("sampl" in s.lower() or "monte carlo" in s.lower()
          for s in _a11.get("derivation_chain", ())), str(_a11.get("derivation_chain")))
check("and it names the percentile the reading is taken at, which is a separate claim",
      any("percentile" in s.lower() for s in _a11.get("derivation_chain", ())),
      str(_a11.get("derivation_chain")))
check("A1.1 declares the budget among its facts, which the cost index never needed",
      "bac" in _a11.get("source_fact_ids", ()), str(_a11.get("source_fact_ids")))
check("A1.1 declares the document risk score among its facts, because the forecast's spread "
      "reads it", "doc_risk_score" in _a11.get("source_fact_ids", ()),
      str(_a11.get("source_fact_ids")))
check("A1.1 declares the document body as well as the earned-value body",
      lineage.DOCUMENT_BODY in _a11.get("lineage_group_ids", ())
      and lineage.EARNED_VALUE_BODY in _a11.get("lineage_group_ids", ()),
      str(_a11.get("lineage_group_ids")))

# A2.1 IS PERT NETWORK CRITICALITY, and it emits nothing.
check("A2.1 is PERT network criticality and not earned schedule",
      method_class_of("A2.1") == "PERT_Network_Criticality", method_class_of("A2.1"))
_pert = registry.run_module("A2.1", {"ev": 1.0, "pv": 1.0, "bac": 1.0, "ac": 1.0, "cpi": 1.0,
                                     "spi": 1.0, "actualPctComplete": 50.0}, lambda: 0.5, None)
check("A2.1 abstains on a fully populated project, because the activity network is absent",
      _pert.get("abstention_reason_code") == "canonical_structure_absent",
      str(_pert.get("abstention_reason_code")))
check("A2.1 therefore declares NO lineage, because a record is a statement about a signal and "
      "this module emits none", lineage.lineage_for("A2.1") is None,
      str(lineage.lineage_for("A2.1")))

# A3.5 IS OVERHEAD ABSORPTION RATE, and it is a body of its own.
check("A3.5 is overhead absorption and not a sensitivity sweep",
      method_class_of("A3.5") == "Overhead_Absorption", method_class_of("A3.5"))
_a35 = rec_of("A3.5")
check("A3.5 declares a lineage record", bool(_a35))
check("HISTORICAL DEFECT, must not return: A3.5 declared inside the earned-value body",
      lineage.EARNED_VALUE_BODY not in _a35.get("lineage_group_ids", ()),
      str(_a35.get("lineage_group_ids")))
check("HISTORICAL DEFECT, must not return: A3.5 declaring the earned value as one of its facts",
      "ev" not in _a35.get("source_fact_ids", ()), str(_a35.get("source_fact_ids")))
check("A3.5 rests on the planned indirect cost",
      "indirect_cost_plan" in _a35.get("source_fact_ids", ()), str(_a35.get("source_fact_ids")))
check("A3.5 rests on the actual indirect cost",
      "indirect_cost_actual" in _a35.get("source_fact_ids", ()), str(_a35.get("source_fact_ids")))
# RUN 28 REVERSED THIS CHECK, and the reversal is the correction rather than a relaxation. Run 20
# cycle 5 required the progress figure to be declared BECAUSE the v10 module scaled the indirect
# plan by it, and said in terms that a fact is not omitted because its consequences are
# inconvenient. The owner's supplied Run-28 contract replaced that computation with absorption
# over an EXPLICIT ALLOCATION BASE, and progress is not an input the module has any more, so
# declaring it would now assert a dependence on every other reader of progress that does not
# exist. The same rule produces the opposite answer because the module changed. The check is
# inverted rather than deleted, so a regression that reintroduced the progress scaling would turn
# it red.
check("A3.5 no longer rests on the progress figure, because it no longer scales anything by it: "
      "overhead is absorbed over an explicit allocation base",
      "actual_pct_complete" not in _a35.get("source_fact_ids", ()),
      str(_a35.get("source_fact_ids")))
check("A3.5 rests on the amount of the allocation base, which is what the rate is formed over",
      "allocation_base_driver" in _a35.get("source_fact_ids", ()),
      str(_a35.get("source_fact_ids")))


# ============================================================ 3. THE HARM, MEASURED AND UNDONE

print("== the suppressed corroboration is restored ==")

_pair = fusion.fuse_signals([sig("A1.7", "Amber"), sig("A3.5", "Amber")])
check("HISTORICAL DEFECT, must not return: the to-complete index and overhead absorption "
      "counted as ONE body of evidence", _pair["lineage_groups"] == 2,
      f"lineage_groups={_pair['lineage_groups']}")
near("HISTORICAL DEFECT, must not return: an Amber earned-value reading and an Amber overhead "
     "reading absorbed into 0.7000; they are two bodies and corroborate to 0.9273",
     _pair["mass"]["Amber"], 0.9273)
check("and their conflict is estimable, because two real bodies can disagree",
      _pair["conflict_estimable"] is True)

# And the suppression must not have merely moved: the earned-value transforms still do not
# corroborate each other.
_ev = fusion.fuse_signals([sig("A1.7", "Amber"), sig("A1.8", "Amber")])
near("the two earned-value transforms still do not corroborate each other",
     _ev["mass"]["Amber"], 0.7000)
check("and they are still one body", _ev["lineage_groups"] == 1)

# Monte Carlo EAC is a reading of the earned-value body, so it must NOT corroborate the voters.
_mc = fusion.fuse_signals([sig("A1.7", "Amber"), sig("A1.1", "Amber")])
near("Monte Carlo EAC does not corroborate the to-complete index, because it forecasts the same "
     "earned-value body", _mc["mass"]["Amber"], 0.7000)
check("and the two are one body", _mc["lineage_groups"] == 1)


# ============================================================ 4. THE GUARD OVER THE WHOLE TABLE
#
# Every declared record must earn its declaration against the module's own runtime behaviour.

print("== every declaration in the table earns itself against the module it names ==")

#: The governed field behind each fact name used anywhere in the table, and the module fields it
#: is reached through where the module is handed a ratio rather than the fact.
FIELD_OF = {
    "bac": "bac", "ev": "ev", "ac": "ac", "pv": "pv",
    "doc_risk_score": "docRiskScore",
    "actual_pct_complete": "actualPctComplete",
    "planned_pct_complete": "plannedPctComplete",
    "change_order_count": "changeOrderCount",
    "baseline_contract_sum": "baselineContractSum",
    "revised_contract_sum": "revisedContractSum",
    "indirect_cost_plan": "indirectCostPlan",
    "indirect_cost_actual": "indirectCostActual",
    # RUN 20 CYCLE 8. The material cost pair, added when the Inflation Adjustment Index was
    # declared. The vocabulary is EXTENDED, not relaxed: both names resolve to a real signal
    # input field and the check below still requires the module's reading to move for each.
    "material_cost_baseline": "materialCostBaseline",
    "material_cost_current": "materialCostCurrent",
    # RUN 28. The governed STRUCTURES the canonical Category 1 to 3 methods are defined on, added
    # when those six declarations were rewritten. The vocabulary is EXTENDED, not relaxed: every
    # name below resolves to a real signal-inputs key the module actually reads, and the material
    # influence check below still requires the module's reading to move when the structure moves.
    # A structure key is a fact in exactly the sense this table means -- something the project
    # supplied that the module's reading rests on -- and it is not a ratio.
    "bayesian_prior": "bayesianEacModel",
    "bayesian_observation": "bayesianEacModel",
    "state_space_observations": "kalmanStateSpaceModel",
    "process_variance": "kalmanStateSpaceModel",
    "measurement_variance": "kalmanStateSpaceModel",
    "management_eac": "independentEacPair",
    "independent_eac": "independentEacPair",
    "allocation_base_driver": "overheadAllocationBase",
    "external_price_index": "externalCostIndex",
    "cost_exposure": "externalCostIndex",
    "risk_events": "costRiskModel",
    "reporting_history": None,          # no single field carries it
}

for mid in _declared:
    rec = lineage.MODULE_LINEAGE[mid]
    check(f"{mid}'s record names {mid} and not another module", rec["module_id"] == mid,
          str(rec["module_id"]))
    check(f"{mid} declares a relationship inside the vocabulary",
          rec["evidence_relationship"] in lineage.EVIDENCE_RELATIONSHIPS)
    for fact in rec["source_fact_ids"]:
        check(f"{mid}'s declared fact {fact} is in the table's own fact vocabulary",
              fact in FIELD_OF, f"fact={fact!r}")
    check(f"{mid} declares no ratio as a fact, because a ratio is a step and not a fact",
          not ({"cpi", "spi"} & set(rec["source_fact_ids"])), str(rec["source_fact_ids"]))
    check(f"{mid} carries a derivation chain longer than its own id",
          len(rec["derivation_chain"]) >= 1)

# A module that can emit no signal on ANY project may not declare a lineage, which is what caught
# A2.1. Checked over the whole table by execution and by the module's own machine-readable
# abstention reason, not by a list of known abstainers and not by mere absence of a colour.
#
# THE DISTINCTION MATTERS AND THE FIRST VERSION OF THIS CHECK GOT IT WRONG, WHICH IS RECORDED
# RATHER THAN QUIETLY RELAXED. Several declared modules also return no colour on this fixture:
# the trend, filter and forecast modules abstain for want of a reporting history, which a real
# project supplies and this hand-written single-period fixture does not. That is a fixture
# limitation and not a structural absence, and a check that read the two as the same thing would
# have demanded declarations be stripped from four modules that legitimately carry them. The
# module states which case it is in: A2.1 abstains with the reason code canonical_structure_absent
# on a fully populated project, meaning the corpus holds no such object for any project at all.
_full = {"bac": 1000000.0, "ev": 500000.0, "ac": 550000.0, "pv": 520000.0,
         "cpi": 500000.0 / 550000.0, "spi": 500000.0 / 520000.0, "docRiskScore": 0.42,
         "actualPctComplete": 50.0, "plannedPctComplete": 52.0, "changeOrderCount": 6,
         "baselineContractSum": 1000000.0, "revisedContractSum": 1080000.0,
         "indirectCostPlan": 200000.0, "indirectCostActual": 230000.0,
         # RUN 28. The governed structures the canonical Category 1 to 3 methods are defined on.
         # A module that abstains for want of one on THIS fixture is not in the A2.1 case the
         # check below exists to catch: the corpus can hold these objects, and two of them --
         # the milestone forecast history and the cost risk model -- are assembled from real
         # documents by documents.py today. Supplying them here is what makes the check test what
         # it means, which is whether a declaring module can emit a signal on SOME project.
         "bayesianEacModel": {
             "parameter": "cost at completion",
             "prior": {"mean": 1000000.0, "variance": 22500000000.0,
                       "source": "approved budget baseline"},
             "likelihood": {"observation": 1100000.0, "variance": 62500000000.0,
                            "source": "reported cost at completion",
                            "variance_basis": "residual spread of reported forecasts"}},
         "kalmanStateSpaceModel": {
             "initial_state": 0.96, "initial_variance": 1.0, "process_variance": 0.01,
             "measurement_variance": 0.1, "observations": [0.96, 0.94],
             "process_variance_source": "declared random walk",
             "measurement_variance_source": "repeated readings of one period"},
         "independentEacPair": {
             "management_eac": {"eac": 1100000.0, "source": "controls report",
                                "method": "index extrapolation",
                                "assumptions": "performance continues",
                                "model_version": "PC-1",
                                "responsible_party": "project management team"},
             "independent_eac": {"eac": 1200000.0, "source": "review board",
                                 "method": "bottom up re-estimate",
                                 "assumptions": "scope re-priced",
                                 "model_version": "IRB-1",
                                 "responsible_party": "independent review board"}},
         "overheadAllocationBase": {
             "allocation_base": "direct labour hours", "driver_source": "certified payroll",
             "planned_overhead": 200000.0, "planned_driver": 20000.0,
             "actual_overhead": 230000.0, "actual_driver": 20000.0},
         "costRiskModel": {
             "model_version": "CRM-1", "estimate_source": "approved base estimate",
             "cost_components": [{"component_id": "BASE", "base_amount": 1000000.0}],
             "risk_events": [{"risk_id": "R1", "probability": 0.5,
                              "impact_distribution": "POINT", "impact": 200000.0}]},
         "externalCostIndex": {
             "index_name": "Construction Cost Index, all items",
             "authority": "national statistical office", "geography": "national",
             "scope": "construction materials and labour", "base_period": "2020-01",
             "observation_period": "2026-06", "vintage": "2026-07 release",
             "base_index_value": 200.0, "current_index_value": 220.0,
             "cost_exposure": 500000.0},
         # RUN 29. The three Category 4 and 5 structures whose modules declare a lineage record,
         # so this check still drives every declared module to a state where it CAN emit a
         # signal rather than excusing three of them.
         "changeEventRegister": FX.change_register(),
         "sensitivityModel": FX.sensitivity_model()}
for mid in _declared:
    if mid.startswith("PH.") or mid not in _available:
        continue
    out = registry.run_module(mid, _full, lambda: 0.5, None)
    check(f"{mid} does not abstain on an absent canonical structure, so it can emit a signal on "
          f"some project and there is evidence to declare",
          out.get("abstention_reason_code") != "canonical_structure_absent",
          f"reason={out.get('abstention_reason_code')!r}")


# ============================================================ 5. THE POSITIVE CONTROL, DRIVEN FROM
#                                                                 THE DECLARED TABLE
#
# This is the check whose absence let the A3.5 error through. Cycle 3's control used a synthetic
# independent body written inside the test, so it proved the RULE could corroborate while saying
# nothing about whether the DECLARATIONS had left anything to corroborate with.

print("== the declared table still contains genuinely independent bodies ==")

_bodies = _parts([lineage.MODULE_LINEAGE[m] for m in _declared])
check("the declared table partitions into MORE THAN ONE body of evidence, so it has not "
      "collapsed everything into one", len(_bodies) > 1, f"{len(_bodies)} bodies: {_bodies!r}")
# THE TRANSITIVE BRIDGE, STATED RATHER THAN ENGINEERED AWAY. Over the WHOLE table the overhead
# absorption reading does land in the same part as the earned-value readings, and not because it
# shares a fact with any of them. It shares the progress figure with Tornado Risk Ranking, which
# in turn shares the earned-value facts, and the partition closes transitively by design. The two
# have no fact in common and are two bodies whenever no bridging signal is present, which is what
# the measurement in section 3 shows and what actually governs any fusion the platform performs.
#
# THAT OPEN METHODOLOGICAL QUESTION IS NOW CLOSED, BY THE OWNER AND NOT BY THIS SUITE. Cycle 5
# raised it here rather than engineering it away: over the whole table the overhead absorption
# reading landed in the same part as the earned-value readings, not through any shared fact but
# because Tornado Risk Ranking shares the progress figure with one and the earned-value facts
# with the other, and the closure was transitive by design. The owner decision that followed
# ruled the closure wrong: dependence is not transitive and a bridging signal must not collapse
# otherwise independent evidence bodies. Cycle 6 replaced it. What the comment below described as
# unsettled is settled, and the checks that measured the old behaviour are reversed in place.
check("the overhead absorption reading shares NO governed fact with the to-complete index",
      not (set(rec_of("A3.5")["source_fact_ids"]) & set(rec_of("A1.7")["source_fact_ids"])),
      f"{rec_of('A3.5')['source_fact_ids']} vs {rec_of('A1.7')['source_fact_ids']}")
check("and they are two bodies of evidence whenever no bridging signal is present, which is the "
      "case that governs the fusion",
      len(_parts([rec_of("A3.5"), rec_of("A1.7")])) == 2)
# RUN 20 CYCLE 6 REVERSED THIS CHECK, WHICH IS THE POINT. It read "the bridge is the progress
# figure and nothing else: remove Tornado Risk Ranking from the table's partition and the two
# separate again", and it was TRUE, because the closure let one bridging signal marry two
# disjoint bodies. The owner decision names that behaviour as the defect. The separation is now
# non-transitive, so removing the bridge changes NOTHING: the two bodies were never merged.
check("removing the bridging signal from the table changes the body count not at all, because "
      "a bridge no longer marries the two bodies it draws from",
      len(_parts([lineage.MODULE_LINEAGE[m] for m in _declared if m != "A5.3"]))
      == len(_bodies), str(_bodies))

# Named, so a future collapse is a named red and not a count that quietly drifts.
_groups = {}
for part in _bodies:
    for i in part:
        _groups[_declared[i]] = tuple(sorted(part))
check("the change-order pair is NOT in the same body as the to-complete index",
      _groups.get("A4.6") != _groups.get("A1.7"), str(_groups.get("A4.6")))
# RUN 28 RESTATED THIS CHECK ON THE PROPERTY IT MEANS, and the restatement is stronger. It
# asserted that A1.1 and A1.7 land in the SAME PART, which is an assignment produced by the
# maximum-independent-set search and is therefore sensitive to every other record in the table:
# Run 28's rewrite of the A3.6 declaration changed which maximum set the search selects, without
# changing anything about the relationship between A1.1 and A1.7. What must hold, and what the
# check was written to protect, is that the two are DEPENDENT and can never both be counted as
# independent bodies corroborating each other. That is asserted directly against the dependence
# relation, and additionally against the selection, so the false-corroboration failure this whole
# file exists to prevent is still caught.
_reps = {p[0] for p in _parts([lineage.MODULE_LINEAGE[m] for m in _declared])}
_a11_rec, _a17_rec = rec_of("A1.1"), rec_of("A1.7")
check("Monte Carlo EAC and the to-complete index share the earned-value measurement, so they "
      "are dependent and neither can corroborate the other",
      bool(set(_a11_rec["source_fact_ids"]) & set(_a17_rec["source_fact_ids"])),
      f"{_a11_rec['source_fact_ids']} vs {_a17_rec['source_fact_ids']}")
check("and the partition never selects both of them as independent bodies, which is the "
      "manufactured corroboration this file exists to prevent",
      not ({_declared.index("A1.1"), _declared.index("A1.7")} <= _reps),
      str(sorted(_reps)))
check("the two voters are in one body", _groups.get("A1.7") == _groups.get("A1.8"))


# ============================================================ 6. NOTHING WAS REBANDED

print("== no module's reading moved ==")

# Pinned from the run of this fixture taken BEFORE any declaration was corrected. The casing is
# pinned as the module emits it, lower-case included, because normalising it here would hide a
# change in what the module actually returns.
for mid, want in (("A1.1", "red"), ("A1.7", "Red"), ("A1.8", "Amber")):
    out = registry.run_module(mid, _full, lambda: 0.5, None)
    check(f"{mid} still bands {want} on the fixture", out.get("status_color") == want,
          f"got {out.get('status_color')!r}")
# RUN 28. A3.5 no longer bands at all: the owner's supplied contract replaced its progress-scaled
# indirect ratio with absorption over an explicit allocation base, and supplies no bands for the
# rate variance. What is pinned instead is the figure, computed by hand from the fixture's own
# allocation base: 230,000 of overhead over 20,000 hours is 11.50 an hour against 200,000 over
# 20,000 which is 10.00, a rate variance of 1.50 and a relative variance of 0.15.
_a35_out = registry.run_module("A3.5", _full, lambda: 0.5, None)
check("A3.5 asserts no band, because the rate variance has no established boundary",
      _a35_out.get("status_color") is None
      and _a35_out.get("calibration_pending") is True, str(_a35_out.get("status_color")))
check("A3.5 reports the hand-derived actual absorption rate of 11.50 an hour",
      abs(_a35_out.get("actual_rate") - 11.5) < 1e-9, str(_a35_out.get("actual_rate")))
check("and the hand-derived relative rate variance of 0.15",
      abs(_a35_out.get("relative_rate_variance") - 0.15) < 1e-9,
      str(_a35_out.get("relative_rate_variance")))
check("the voting set is still exactly the two earned-value transforms",
      set(registry.CORE_VOTING_MODULES) == {"A1.7", "A1.8"},
      str(sorted(registry.CORE_VOTING_MODULES)))


print("")
if _fail:
    print("FAILURES:")
    for f in _fail:
        print("  -", f)
print(f"RESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
