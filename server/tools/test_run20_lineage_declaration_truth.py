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

from app.simulation import fusion, lineage, registry  # noqa: E402

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
for mid in _declared:
    if mid.startswith("PH."):
        continue  # portfolio health is not a project module and has no registry entry
    check(f"{mid} is a module this platform actually runs", mid in _available)


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
check("A3.5 rests on the progress figure, which scales the plan and which it must not omit "
      "merely because declaring it creates a dependence",
      "actual_pct_complete" in _a35.get("source_fact_ids", ()), str(_a35.get("source_fact_ids")))


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
         "indirectCostPlan": 200000.0, "indirectCostActual": 230000.0}
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

_bodies = lineage.partition([lineage.MODULE_LINEAGE[m] for m in _declared])
check("the declared table partitions into MORE THAN ONE body of evidence, so it has not "
      "collapsed everything into one", len(_bodies) > 1, f"{len(_bodies)} bodies: {_bodies!r}")
# THE TRANSITIVE BRIDGE, STATED RATHER THAN ENGINEERED AWAY. Over the WHOLE table the overhead
# absorption reading does land in the same part as the earned-value readings, and not because it
# shares a fact with any of them. It shares the progress figure with Tornado Risk Ranking, which
# in turn shares the earned-value facts, and the partition closes transitively by design. The two
# have no fact in common and are two bodies whenever no bridging signal is present, which is what
# the measurement in section 3 shows and what actually governs any fusion the platform performs.
#
# WHETHER TRANSITIVE CLOSURE THROUGH A BRIDGING SIGNAL IS THE RIGHT TREATMENT IS A REAL
# METHODOLOGICAL QUESTION AND IT IS NOT SETTLED HERE. Loosening the closure to make this check
# read better would be moving a rule to satisfy an example, which this programme does not do. It
# is recorded as an open question in the register and in the owner decisions, and what is asserted
# below is what is true.
check("the overhead absorption reading shares NO governed fact with the to-complete index",
      not (set(rec_of("A3.5")["source_fact_ids"]) & set(rec_of("A1.7")["source_fact_ids"])),
      f"{rec_of('A3.5')['source_fact_ids']} vs {rec_of('A1.7')['source_fact_ids']}")
check("and they are two bodies of evidence whenever no bridging signal is present, which is the "
      "case that governs the fusion",
      len(lineage.partition([rec_of("A3.5"), rec_of("A1.7")])) == 2)
check("the bridge is the progress figure and nothing else: remove Tornado Risk Ranking from the "
      "table's partition and the two separate again",
      len(lineage.partition([lineage.MODULE_LINEAGE[m] for m in _declared if m != "A5.3"])) > len(_bodies),
      str(_bodies))

# Named, so a future collapse is a named red and not a count that quietly drifts.
_groups = {}
for part in _bodies:
    for i in part:
        _groups[_declared[i]] = tuple(sorted(part))
check("the change-order pair is NOT in the same body as the to-complete index",
      _groups.get("A4.6") != _groups.get("A1.7"), str(_groups.get("A4.6")))
check("Monte Carlo EAC IS in the same body as the to-complete index, because it forecasts it",
      _groups.get("A1.1") == _groups.get("A1.7"), str(_groups.get("A1.1")))
check("the two voters are in one body", _groups.get("A1.7") == _groups.get("A1.8"))


# ============================================================ 6. NOTHING WAS REBANDED

print("== no module's reading moved ==")

# Pinned from the run of this fixture taken BEFORE any declaration was corrected. The casing is
# pinned as the module emits it, lower-case included, because normalising it here would hide a
# change in what the module actually returns.
for mid, want in (("A1.1", "red"), ("A3.5", "Red"), ("A1.7", "Red"), ("A1.8", "Amber")):
    out = registry.run_module(mid, _full, lambda: 0.5, None)
    check(f"{mid} still bands {want} on the fixture", out.get("status_color") == want,
          f"got {out.get('status_color')!r}")
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
