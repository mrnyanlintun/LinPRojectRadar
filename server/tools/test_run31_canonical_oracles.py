"""
RUN 31 CANONICAL ORACLES.

EVERY EXPECTED VALUE IN THIS FILE COMES FROM THE SUPPLIED CONTRACT OR FROM A HAND CALCULATION,
NEVER FROM PRODUCTION (section 45). Where the contract states a number -- 0.20, 0.75, 0.92, 3.0,
0.9, 2/3, delay 5 -- that number is written as a literal below and production must reproduce it.
Where the contract states a rule and an evidence combination, the expected disposition is the
one the rule and evidence imply, computed by hand before the code was run.

The ABM event trace is hand-computed in the block comment above `abm_trace_oracle` and asserted
transition by transition, so a model that reaches the right terminal state by the wrong sequence
of transitions still fails.
"""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.simulation import canonical_v6 as V6            # noqa: E402
from app.simulation import regulatory as REG             # noqa: E402
from app.simulation.abm import (                         # noqa: E402
    AUTHORIZED_BY_OWNER, BLOCKED_PROCEDURE_INCOMPLETE, BLOCKED_UNQUALIFIED_EVIDENCE, DEFERRED,
    NO_ACTION_ABSTAINING_SIGNAL, REQUEST_EVIDENCE, model_from,
)
from app.simulation.canonical import StructureAbsent     # noqa: E402
from app.simulation.qualified_evidence import (          # noqa: E402
    CONSISTENT, FUTURE_DATED, MATERIAL_CONFLICT, STALE, TIMELY,
)

PASS = 0
FAIL = 0
FAILURES = []


def check(name, got, want):
    global PASS, FAIL
    if got == want:
        PASS += 1
    else:
        FAIL += 1
        FAILURES.append(f"{name}: expected {want!r}, got {got!r}")


def check_true(name, cond):
    check(name, bool(cond), True)


# =============================================================================================
# 9.1 MISSING DATA INDEX. Contract: 10 applicable mandatory fields, 2 missing -> 0.20.
# =============================================================================================
fields = [f"f{i}" for i in range(1, 11)]
values = {f: 0 for f in fields}          # ZERO IS A VALUE, deliberately, for every field
del values["f9"], values["f10"]          # two absent -> missing
mdi = V6.missing_data_index({"contract_id": "USE-A", "contract_version": "1",
                             "required_fields": fields, "values": values})
check("9.1 missing fraction 2/10", mdi["missing_fraction"], 0.20)
check("9.1 applicable denominator", mdi["applicable_required_count"], 10)
check("9.1 zero-valued fields are not missing", mdi["missing_fields"], ["f10", "f9"])

# zero is a value (fault 10's intended defect, asserted positively here)
z = V6.missing_data_index({"required_fields": ["a"], "values": {"a": 0}})
check("9.1 a required field valued zero is present", z["missing_fraction"], 0.0)
# null is missing; absent is missing
n = V6.missing_data_index({"required_fields": ["a", "b"], "values": {"a": None}})
check("9.1 null and absent are both missing", n["missing_fraction"], 1.0)
# not-applicable fields leave the denominator (fault 9)
na = V6.missing_data_index({"required_fields": ["a", "b", "c"], "values": {"a": 1},
                            "not_applicable_fields": ["b", "c"]})
check("9.1 not-applicable fields leave the denominator", na["applicable_required_count"], 1)
check("9.1 not-applicable fields are not missing", na["missing_fraction"], 0.0)
# optional fields never enter
opt = V6.missing_data_index({"required_fields": ["a"], "values": {"a": 1, "opt1": None}})
check("9.1 optional fields never enter the denominator", opt["applicable_required_count"], 1)
# invalid mandatory fields are separate from missing
inv = V6.missing_data_index({"required_fields": ["a", "b"], "values": {"a": "xx", "b": 1},
                             "invalid_fields": ["a"]})
check("9.1 invalid is not counted as missing", inv["missing_fraction"], 0.0)
check("9.1 invalid is separately identified", inv["invalid_fields"], ["a"])
# critical missing survives a tiny fraction
crit = V6.missing_data_index({"required_fields": [f"f{i}" for i in range(20)],
                              "values": {f"f{i}": 1 for i in range(1, 20)},
                              "critical_fields": ["f0"]})
check("9.1 tiny fraction", round(crit["missing_fraction"], 4), 0.05)
check("9.1 critical missing is preserved beside a tiny fraction", crit["critical_missing"], ["f0"])
# no applicable requirement -> governed state, no division
noapp = V6.missing_data_index({"required_fields": ["a"], "not_applicable_fields": ["a"]})
check("9.1 no applicable requirement does not divide by zero",
      noapp["disposition"], "NO_APPLICABLE_REQUIREMENT")
check("9.1 no applicable requirement returns no fraction", noapp["missing_fraction"], None)
try:
    V6.missing_data_index({"values": {}})
    check("9.1 absent contract abstains", "no raise", "StructureAbsent")
except StructureAbsent:
    check("9.1 absent contract abstains", "StructureAbsent", "StructureAbsent")

# =============================================================================================
# 9.2 DATA TIMELINESS. Contract: allowed age 30 days; 20 -> TIMELY, 40 -> STALE, -2 -> FUTURE.
# =============================================================================================
RULE30 = {"allowed_age_days": 30, "boundary": "inclusive", "version": "fr-v1"}


def timeliness(age_days):
    from datetime import date, timedelta
    ev = date(2026, 8, 16)
    return V6.data_timeliness({"evaluation_date": ev.isoformat(),
                               "effective_date": (ev - timedelta(days=age_days)).isoformat(),
                               "date_field": "effective_date", "source_class": "COST_REPORT",
                               "use": "current_period_decision", "freshness_rule": RULE30})


check("9.2 age 20 against a 30-day rule", timeliness(20)["timeliness_status"], TIMELY)
check("9.2 age 20 reports its age", timeliness(20)["age_days"], 20)
check("9.2 age 40 against a 30-day rule", timeliness(40)["timeliness_status"], STALE)
check("9.2 age 40 reports its age", timeliness(40)["age_days"], 40)
check("9.2 age -2 is future dated", timeliness(-2)["timeliness_status"], FUTURE_DATED)
check("9.2 exact boundary inclusive", timeliness(30)["timeliness_status"], TIMELY)
excl = dict(RULE30, boundary="exclusive")
check("9.2 exact boundary exclusive",
      V6.data_timeliness({"evaluation_date": "2026-08-16", "effective_date": "2026-07-17",
                          "freshness_rule": excl})["timeliness_status"], STALE)
check("9.2 missing date is insufficient evidence",
      V6.data_timeliness({"evaluation_date": "2026-08-16",
                          "freshness_rule": RULE30})["timeliness_status"], "INSUFFICIENT_EVIDENCE")
try:
    V6.data_timeliness({"evaluation_date": "2026-08-16", "effective_date": "2026-08-01"})
    check("9.2 no governed freshness rule abstains", "no raise", "StructureAbsent")
except StructureAbsent:
    check("9.2 no governed freshness rule abstains", "StructureAbsent", "StructureAbsent")
try:
    V6.data_timeliness({"evaluation_date": "2026-08-16", "effective_date": "2026-08-01",
                        "freshness_rule": {"allowed_age_days": 30}})
    check("9.2 undeclared boundary abstains", "no raise", "StructureAbsent")
except StructureAbsent:
    check("9.2 undeclared boundary abstains", "StructureAbsent", "StructureAbsent")
# SOURCE-CLASS SPECIFICITY: the same record is timely for one use and stale for another.
same = {"evaluation_date": "2026-08-16", "effective_date": "2026-07-17"}
check("9.2 same record timely under a 60-day rule",
      V6.data_timeliness(dict(same, use="historical_analysis",
                              freshness_rule={"allowed_age_days": 60, "boundary": "inclusive"}
                              ))["timeliness_status"], TIMELY)
check("9.2 same record stale under a 7-day rule",
      V6.data_timeliness(dict(same, use="current_period_decision",
                              freshness_rule={"allowed_age_days": 7, "boundary": "inclusive"}
                              ))["timeliness_status"], STALE)

# =============================================================================================
# 9.3 SOURCE RELIABILITY. No governed mapping -> weight NONE, never 1.
# =============================================================================================
nr = V6.source_reliability({"source_authority": "unknown", "verification_status": "unverified"})
check("9.3 no governed rubric yields no weight", nr["reliability_weight"], None)
check("9.3 no governed rubric is stated as such", nr["disposition"], "NO_GOVERNED_MAPPING")
check_true("9.3 component evidence is still reported", nr["components"]["source_authority"])
check_true("9.3 BAC is not a reliability component", "bac" not in str(nr["components"]).lower())

SYNTH_RUBRIC = {
    "version": "SYNTHETIC_RESEARCH_RUBRIC-v1", "basis": "test-only mechanics proof",
    "calibration_source": "NONE", "effective_date": "2026-08-16",
    "not_for_operational_weighting": True,
    "scores": {"verification_status": {"unverified": 0.0, "corroborated": 0.5, "verified": 1.0},
               "source_authority": {"unknown": 0.0, "secondary": 0.5, "system_of_record": 1.0}},
}


def rel(**kw):
    return V6.source_reliability(dict({"rubric": SYNTH_RUBRIC}, **kw))["reliability_weight"]


base_attrs = {"source_authority": "system_of_record"}
unver = rel(verification_status="unverified", **base_attrs)
corr = rel(verification_status="corroborated", **base_attrs)
ver = rel(verification_status="verified", **base_attrs)
check_true("9.3 monotone: verified is not below unverified under the supplied rubric",
           ver >= corr >= unver)
check("9.3 unknown source scores lowest under the supplied rubric",
      rel(verification_status="verified", source_authority="unknown"), 1.0)
check("9.3 system-of-record source", rel(verification_status="verified",
                                         source_authority="system_of_record"), 2.0)
check("9.3 the synthetic rubric is labelled not-for-operational-weighting",
      V6.source_reliability({"rubric": SYNTH_RUBRIC})["not_for_operational_weighting"], True)
try:
    V6.source_reliability({"rubric": {"scores": {"a": {"b": 1}}}})
    check("9.3 unversioned rubric abstains", "no raise", "StructureAbsent")
except StructureAbsent:
    check("9.3 unversioned rubric abstains", "StructureAbsent", "StructureAbsent")
# superseded / conflicting records remain visible as components
sc = V6.source_reliability({"superseded": True, "conflicting_records": ["DOC-1 vs DOC-2"]})
check("9.3 superseded state is reported", sc["components"]["superseded"], True)
check("9.3 conflicting authoritative records are reported",
      sc["components"]["conflicting_records"], ["DOC-1 vs DOC-2"])

# =============================================================================================
# 9.4 AUDIT TRAIL COMPLETENESS. Contract: 10 required, 9 present -> ATC 0.9; critical -> False.
# =============================================================================================
SCHEMA = {"version": "audit-v1",
          "mandatory_critical": ["evidence_id", "method_version", "judgment_id", "actor",
                                 "timestamp"],
          "mandatory_noncritical": ["disposition", "linkage", "period", "source", "reviewer"]}
all_ten = SCHEMA["mandatory_critical"] + SCHEMA["mandatory_noncritical"]
nine = [e for e in all_ten if e != "reviewer"]          # missing element is NONCRITICAL
atc = V6.audit_trail_completeness({"audit_schema": SCHEMA, "present_elements": nine})
check("9.4 ATC 9 of 10", atc["atc"], 0.9)
check("9.4 a missing mandatory noncritical element is not complete", atc["audit_complete"], False)
full = V6.audit_trail_completeness({"audit_schema": SCHEMA, "present_elements": all_ten})
check("9.4 complete chain ATC", full["atc"], 1.0)
check("9.4 complete chain is complete", full["audit_complete"], True)
# missing CRITICAL element
nine_c = [e for e in all_ten if e != "method_version"]
critm = V6.audit_trail_completeness({"audit_schema": SCHEMA, "present_elements": nine_c})
check("9.4 missing critical element ATC", critm["atc"], 0.9)
check("9.4 missing critical element is not complete", critm["audit_complete"], False)
check("9.4 missing method version is named", critm["critical_missing"], ["method_version"])
# ADDING 100 OPTIONAL FIELDS MUST NOT COMPENSATE (fault 17)
padded = V6.audit_trail_completeness({"audit_schema": SCHEMA,
                                      "present_elements": nine_c + [f"opt{i}" for i in range(100)]})
check("9.4 100 optional fields do not change ATC", padded["atc"], 0.9)
check("9.4 100 optional fields do not make it complete", padded["audit_complete"], False)
# missing optional only
check("9.4 a missing optional element leaves the chain complete",
      V6.audit_trail_completeness({"audit_schema": SCHEMA, "present_elements": all_ten,
                                   })["audit_complete"], True)
# broken links (fault 18) and impossible chronology (fault 19)
bl = V6.audit_trail_completeness({"audit_schema": SCHEMA, "present_elements": all_ten,
                                  "links": {"evidence_to_signal": False, "signal_to_judgment": True}})
check("9.4 a broken evidence->signal link is not complete", bl["audit_complete"], False)
check("9.4 the broken link is named", bl["broken_links"], ["evidence_to_signal"])
bl2 = V6.audit_trail_completeness({"audit_schema": SCHEMA, "present_elements": all_ten,
                                   "links": {"signal_to_judgment": False}})
check("9.4 a broken signal->judgment link is not complete", bl2["audit_complete"], False)
chron = V6.audit_trail_completeness({"audit_schema": SCHEMA, "present_elements": all_ten,
                                     "chronology_valid": False})
check("9.4 impossible chronology is not complete", chron["audit_complete"], False)
# missing required authority
noauth = V6.audit_trail_completeness({"audit_schema": SCHEMA,
                                      "present_elements": [e for e in all_ten if e != "actor"]})
check("9.4 missing required authority is not complete", noauth["audit_complete"], False)
check_true("9.4 BAC is not an audit element", "bac" not in str(SCHEMA).lower())

# =============================================================================================
# 9.5 INFORMATION COMPLETENESS. Contract: 8 applicable required components, 6 usable -> 0.75.
# =============================================================================================
def comp(i, present=True, usable=True, critical=False, applicable=True):
    return {"component_id": f"C{i}", "domain": f"D{i}", "applicable": applicable,
            "required": True, "present": present, "critical": critical,
            "mandatory_fields": ["m1"], "values": {"m1": (1 if usable else None)}}


pkg8 = [comp(i) for i in range(1, 7)] + [comp(7, present=False), comp(8, present=False)]
ic = V6.information_completeness({"package_id": "PKG-1", "components": pkg8})
check("9.5 coverage 6 of 8", ic["information_completeness"], 0.75)
check("9.5 applicable required denominator", ic["applicable_required_components"], 8)
# a filename with every mandatory field missing is NOT usable
unus = V6.information_completeness({"components": [comp(1), comp(2, usable=False)]})
check("9.5 a present but empty component is not usable", unus["information_completeness"], 0.5)
check("9.5 the unusable component is named", unus["unusable_components"], ["C2"])
# not-applicable components leave the denominator
naC = V6.information_completeness({"components": [comp(1), comp(2, applicable=False)]})
check("9.5 not-applicable components leave the denominator",
      naC["applicable_required_components"], 1)
# critical absence stays visible
critp = V6.information_completeness({"components": [comp(1), comp(2, present=False, critical=True)]})
check("9.5 critical package absence stays visible", critp["missing_critical_domains"], ["C2"])

# --------- THE 9.1 vs 9.5 NONREDUNDANCY WITNESS (section 27) ---------------------------------
# Every document that IS present has complete fields; one entire required domain is absent.
present_fields = {"required_fields": ["cost_a", "cost_b"], "values": {"cost_a": 1, "cost_b": 2}}
package_missing_domain = {"package_id": "PKG-NR", "components": [
    {"component_id": "COST", "required": True, "present": True, "mandatory_fields": ["cost_a"],
     "values": {"cost_a": 1}},
    {"component_id": "SCHEDULE", "required": True, "present": True, "mandatory_fields": ["sd"],
     "values": {"sd": "2026-01-01"}},
    {"component_id": "SAFETY", "required": True, "present": False, "critical": True,
     "mandatory_fields": ["hours"], "values": {}},
]}
nr_proof = V6.nonredundancy(package_missing_domain, present_fields)
check("9.1/9.5 field-level missingness is complete", nr_proof["field_level_missing_fraction"], 0.0)
check("9.1/9.5 package coverage is incomplete", round(nr_proof["package_coverage"], 4), 0.6667)
check("9.1/9.5 the two states are distinguishable", nr_proof["distinguishable"], True)
check("9.1/9.5 the absent domain is named", nr_proof["missing_domains"], ["SAFETY"])

# =============================================================================================
# 9.6 CROSS-DOCUMENT CONSISTENCY. Contract oracles A and B.
# =============================================================================================
def bac_fact(b_value, tol=0.02, b_period="2026-07", a_period="2026-07"):
    return {"facts": [{"fact_id": "BAC", "reference_source": "A",
                       "tolerance": {"relative": tol}, "tolerance_version": "tol-v1",
                       "observations": [
                           {"source_id": "A", "value": 100.0, "units": "USD",
                            "period": a_period, "revision": "R1"},
                           {"source_id": "B", "value": b_value, "units": "USD",
                            "period": b_period, "revision": "R1"}]}]}


oa = V6.cross_document_consistency(bac_fact(100.0))
check("9.6 oracle A: 100 vs 100 is consistent", oa["comparisons"][0]["result"], CONSISTENT)
check("9.6 oracle A: no conflict recorded", oa["material_conflicts"], [])
ob = V6.cross_document_consistency(bac_fact(110.0))
check("9.6 oracle B: 100 vs 110 at 2% is a material conflict",
      ob["comparisons"][0]["result"], MATERIAL_CONFLICT)
check("9.6 oracle B: relative difference is 10%",
      round(ob["comparisons"][0]["relative_difference"], 6), 0.1)
check("9.6 oracle B: the conflict is preserved", len(ob["material_conflicts"]), 1)
check("9.6 oracle B: both values survive in the conflict row",
      (ob["material_conflicts"][0]["reference_value"], ob["material_conflicts"][0]["value"]),
      (100.0, 110.0))
# NEVER AVERAGED (fault 22): 105 must appear nowhere in the result.
check("9.6 the conflict is not averaged to 105", "105" in str(ob), False)
# different periods are NOT_COMPARABLE, not inconsistent (fault 23)
dp = V6.cross_document_consistency(bac_fact(110.0, b_period="2026-06"))
check("9.6 different reporting periods are not comparable",
      dp["comparisons"][0]["result"], "NOT_COMPARABLE")
check("9.6 different periods raise no conflict", dp["material_conflicts"], [])
# no governed tolerance -> not comparable, none invented
nt = V6.cross_document_consistency({"facts": [{"fact_id": "BAC", "reference_source": "A",
    "observations": [{"source_id": "A", "value": 100.0, "units": "USD", "period": "P"},
                     {"source_id": "B", "value": 110.0, "units": "USD", "period": "P"}]}]})
check("9.6 no governed tolerance is not comparable",
      nt["comparisons"][0]["result"], "NOT_COMPARABLE")
# categorical exact match
cat = V6.cross_document_consistency({"facts": [{"fact_id": "STATUS", "reference_source": "A",
    "observations": [{"source_id": "A", "value": "OPEN", "units": None, "period": "P"},
                     {"source_id": "B", "value": "CLOSED", "units": None, "period": "P"}]}]})
check("9.6 categorical mismatch is a material conflict",
      cat["comparisons"][0]["result"], MATERIAL_CONFLICT)

# =============================================================================================
# 9.7 REPORTING FREQUENCY. Contract: due day 30/60/90.
# =============================================================================================
PERIODS = [{"period_id": "P1", "due_date": "2026-01-30"},
           {"period_id": "P2", "due_date": "2026-03-01"},   # "day 60"
           {"period_id": "P3", "due_date": "2026-03-31"}]   # "day 90"


def cadence(history, extensions=None):
    return V6.reporting_frequency({"report_class": "MONTHLY_EVMS", "expected_periods": PERIODS,
                                   "report_history": history,
                                   "approved_extensions": extensions or {}})


perfect = cadence([{"period_id": "P1", "received_date": "2026-01-30"},
                   {"period_id": "P2", "received_date": "2026-03-01"},
                   {"period_id": "P3", "received_date": "2026-03-31"}])
check("9.7 perfect coverage", perfect["reporting_coverage"], 1.0)
check("9.7 perfect on-time rate", perfect["on_time_reporting_rate"], 1.0)
missed = cadence([{"period_id": "P1", "received_date": "2026-01-30"},
                  {"period_id": "P3", "received_date": "2026-03-31"}])
check("9.7 one missed period coverage 2/3", round(missed["reporting_coverage"], 6),
      round(2 / 3, 6))
dup = cadence([{"period_id": "P1", "received_date": "2026-01-30"},
               {"period_id": "P1", "received_date": "2026-01-30"},
               {"period_id": "P2", "received_date": "2026-03-01"},
               {"period_id": "P3", "received_date": "2026-03-31"}])
check("9.7 a duplicate report does not improve coverage", dup["reporting_coverage"], 1.0)
check("9.7 the duplicate is recorded as ignored", dup["duplicate_reports_ignored"], 1)
late = cadence([{"period_id": "P1", "received_date": "2026-01-30"},
                {"period_id": "P2", "received_date": "2026-03-06"},   # "day 65" vs due day 60
                {"period_id": "P3", "received_date": "2026-03-31"}])
check("9.7 late report still counts for coverage", late["reporting_coverage"], 1.0)
check("9.7 late report on-time rate 2/3", round(late["on_time_reporting_rate"], 6),
      round(2 / 3, 6))
check("9.7 the late period is named late", late["periods"][1]["status"], "LATE")
ext = cadence([{"period_id": "P1", "received_date": "2026-01-30"},
               {"period_id": "P2", "received_date": "2026-03-06"},
               {"period_id": "P3", "received_date": "2026-03-31"}],
              extensions={"P2": "2026-03-06"})
check("9.7 an approved extension makes the same report on time",
      ext["on_time_reporting_rate"], 1.0)
check("9.7 the revised due date is recorded",
      ext["periods"][1]["due_date_revised_by_approved_extension"], True)

# --------- THE 9.2 vs 9.7 NONREDUNDANCY WITNESS (section 29) ---------------------------------
# One record, perfectly fresh today, whose recurring cadence has a missed period; and one record
# that is stale today while every expected report was filed on time. Neither is derivable from
# the other's input, and the two answers move independently.
fresh_but_missed = (timeliness(1)["timeliness_status"], round(missed["reporting_coverage"], 6))
check("9.2/9.7 fresh now, cadence incomplete", fresh_but_missed, (TIMELY, round(2 / 3, 6)))
stale_but_complete = (timeliness(40)["timeliness_status"], perfect["reporting_coverage"])
check("9.2/9.7 stale now, cadence complete", stale_but_complete, (STALE, 1.0))
check("9.2/9.7 freshness and cadence do not collapse to one result",
      fresh_but_missed == stale_but_complete, False)

# =============================================================================================
# 8.2 EVMS APPLICABILITY. Contract cases A, B, C, D.
# =============================================================================================
caseA = V6.evms_applicability({"acquisition_id": "ACQ-1", "federal_context": True,
                               "acquisition_designation": "development", "major_acquisition": True,
                               "agency": "GSA", "evidence_source": "contract file"})
check("8.2 Case A: major for development is APPLICABLE", caseA["applicability"], REG.APPLICABLE)
caseB = V6.evms_applicability({"acquisition_id": "ACQ-2", "federal_context": True,
                               "acquisition_designation": "production", "major_acquisition": False,
                               "agency": "GSA", "agency_procedure_requires_evms": True})
check("8.2 Case B: agency procedure requires EVMS", caseB["applicability"], REG.APPLICABLE)
caseC = V6.evms_applicability({"acquisition_id": "ACQ-3", "federal_context": True,
                               "acquisition_designation": "production", "agency": "GSA",
                               "evms_not_applicable_established": True})
check("8.2 Case C: established non-applicability", caseC["applicability"], REG.NOT_APPLICABLE)
caseD = V6.evms_applicability({"acquisition_id": "ACQ-4", "federal_context": True,
                               "agency": None, "acquisition_designation": None})
check("8.2 Case D: incomplete designation is insufficient evidence",
      caseD["applicability"], REG.INSUFFICIENT_EVIDENCE)
caseD2 = V6.evms_applicability({"acquisition_id": "ACQ-5", "federal_context": True,
                                "acquisition_designation": "development", "agency": "GSA",
                                "conflicting_evidence": ["clause says applies; agency says not"]})
check("8.2 Case D': conflicting evidence requires review",
      caseD2["applicability"], REG.REVIEW_REQUIRED)
# BAC / CPI ARE NOT READ (fault 36)
bac_only = V6.evms_applicability({"acquisition_id": "A", "bac": 500_000_000, "cpi": 0.7})
check("8.2 a BAC alone establishes nothing", bac_only["applicability"], REG.INSUFFICIENT_EVIDENCE)
check("8.2 no dollar threshold appears in the result", "500000000" in str(bac_only), False)
# missing designation/clause never becomes APPLICABLE (fault 37)
check("8.2 missing designation is never APPLICABLE",
      V6.evms_applicability({"federal_context": True, "agency": "GSA"})["applicability"]
      != REG.APPLICABLE, True)
check("8.2 the result names the rule applied", caseA["rule_source"], "FAR 34.201")
check("8.2 the result carries the edition", caseA["rule_version"], "FAC 2026-01")
check("8.2 no FAR-compliant claim is made", REG.prohibited_claims_in(caseA["statement"]), [])

# =============================================================================================
# 8.3 A-11 CONFORMANCE. Contract fixture R1/R2/R3.
# =============================================================================================
A11 = {"a11_edition": "A-11 2025-08-29", "rules": [
    {"rule_id": "R1", "section": "Part 7", "effective_date": "2025-08-29", "summary": "s",
     "applicable": True, "required_evidence": ["e1"], "evidence": {"e1": "present"},
     "reviewer": "agency reviewer", "satisfied": True},
    {"rule_id": "R2", "section": "Part 7", "effective_date": "2025-08-29", "summary": "s",
     "applicable": True, "required_evidence": ["e1"], "evidence": {},
     "reviewer": "agency reviewer", "satisfied": True},
    {"rule_id": "R3", "section": "Part 7", "effective_date": "2025-08-29", "summary": "s",
     "applicable": False, "required_evidence": ["e1"], "evidence": {"e1": "present"},
     "reviewer": "agency reviewer", "satisfied": True},
]}
a11 = V6.a11_conformance(A11)
byid = {r.get("rule_id"): r for r in a11["rule_results"]}
check("8.3 R1 applicable with evidence is SATISFIED", byid["R1"]["result"], REG.SATISFIED)
check("8.3 R2 applicable without evidence is INSUFFICIENT_EVIDENCE",
      byid["R2"]["result"], REG.INSUFFICIENT_EVIDENCE)
check("8.3 R2 names the missing evidence", byid["R2"]["missing_evidence"], ["e1"])
check("8.3 R3 not applicable is NOT_APPLICABLE", byid["R3"]["result"], REG.NOT_APPLICABLE)
check("8.3 no global A-11 claim is made", a11["global_a11_claim"], None)
check("8.3 the result declares itself a configured subset", a11["subset_only"], True)
# superseded / wrong edition (fault 39)
sup = V6.a11_conformance(dict(A11, a11_edition="A-11 2019-06-28"))
check("8.3 a superseded edition is REVIEW_REQUIRED, not SATISFIED",
      {r["result"] for r in sup["rule_results"]}, {REG.REVIEW_REQUIRED})
# missing edition
mis = V6.a11_conformance(dict(A11, a11_edition=None))
check("8.3 a missing edition never yields SATISFIED",
      any(r["result"] == REG.SATISFIED for r in mis["rule_results"]), False)
# reviewer missing where required
norev = V6.a11_conformance({"a11_edition": "A-11 2025-08-29", "rules": [
    dict(A11["rules"][0], reviewer=None)]})
check("8.3 a missing reviewer is REVIEW_REQUIRED",
      norev["rule_results"][0]["result"], REG.REVIEW_REQUIRED)
# no evidence at all never becomes SATISFIED (fault 38)
noev = V6.a11_conformance({"a11_edition": "A-11 2025-08-29", "rules": [
    dict(A11["rules"][0], evidence={})]})
check("8.3 no evidence never becomes SATISFIED",
      noev["rule_results"][0]["result"], REG.INSUFFICIENT_EVIDENCE)

# =============================================================================================
# 8.4 EVMS REPORTING. Contract oracles.
# =============================================================================================
APPLIC = {"applicability": REG.APPLICABLE}
ontime = V6.evms_reporting({"clause_id": "52.234-4", "required_cadence": "monthly",
                            "required_artifacts_expected": 4, "required_artifacts_received": 4,
                            "due_date": "2026-07-31", "received_date": "2026-07-31"}, APPLIC)
check("8.4 on time and complete: fraction 1", ontime["completeness_fraction"], 1.0)
check("8.4 on time and complete: delay 0", ontime["reporting_delay_days"], 0)
check("8.4 on time and complete: satisfied", ontime["result"], REG.SATISFIED)
lateR = V6.evms_reporting({"clause_id": "52.234-4", "required_cadence": "monthly",
                           "required_artifacts_expected": 4, "required_artifacts_received": 4,
                           "due_date": "2026-07-31", "received_date": "2026-08-05"}, APPLIC)
check("8.4 late: delay 5 days", lateR["reporting_delay_days"], 5)
incomp = V6.evms_reporting({"clause_id": "52.234-4", "required_cadence": "monthly",
                            "required_artifacts_expected": 4, "required_artifacts_received": 3,
                            "due_date": "2026-07-31", "received_date": "2026-07-31"}, APPLIC)
check("8.4 incomplete: fraction 0.75", incomp["completeness_fraction"], 0.75)
check("8.4 incomplete is not satisfied", incomp["result"], REG.NOT_SATISFIED)
naR = V6.evms_reporting({"clause_id": "52.234-4", "required_cadence": "monthly"},
                        {"applicability": REG.NOT_APPLICABLE})
check("8.4 EVMS not applicable -> reporting NOT_APPLICABLE", naR["result"], REG.NOT_APPLICABLE)
check("8.4 a not-applicable project receives no violation",
      naR["result"] == REG.NOT_SATISFIED, False)
unres = V6.evms_reporting({"clause_id": "52.234-4", "required_cadence": "monthly"}, None)
check("8.4 unresolved applicability does not manufacture compliance",
      unres["result"], REG.INSUFFICIENT_EVIDENCE)
noclause = V6.evms_reporting({"required_cadence": "monthly"}, APPLIC)
check("8.4 a missing clause does not return a positive result",
      noclause["result"], REG.INSUFFICIENT_EVIDENCE)
missing_report = V6.evms_reporting({"clause_id": "52.234-4", "required_cadence": "monthly",
                                    "required_artifacts_expected": 4,
                                    "required_artifacts_received": 4,
                                    "due_date": "2026-07-31"}, APPLIC)
check("8.4 a missing report is not counted complete", missing_report["result"], REG.NOT_SATISFIED)
# CPI/SPI cannot establish anything (fault 40)
cpi_only = V6.evms_reporting({"cpi": 1.2, "spi": 1.1}, APPLIC)
check("8.4 CPI/SPI alone do not establish reporting conformance",
      cpi_only["result"], REG.INSUFFICIENT_EVIDENCE)

# =============================================================================================
# 8.5 CONTRACT MODIFICATION GOVERNANCE.
# =============================================================================================
def mod(**kw):
    base = {"modification_id": "M1", "contract_id": "C1", "federal_context": True,
            "modification_type": "bilateral", "executing_official": "CO Jane Doe",
            "authority_evidence": "warrant 1102-4471", "signed_parties": ["GOV", "CTR"],
            "sf30_applicable": True, "written_instrument": "SF30",
            "reviewer": "contracting officer", "officer_authority_current": True}
    base.update(kw)
    return V6.modification_governance({"contract_id": "C1", "modifications": [base]}
                                      )["modification_results"][0]


ab = mod()
check("8.5 authorized bilateral: authority satisfied", ab["authority_check"]["result"],
      REG.SATISFIED)
check("8.5 authorized bilateral: type satisfied", ab["type_check"]["result"], REG.SATISFIED)
check("8.5 authorized bilateral: form satisfied", ab["form_check"]["result"], REG.SATISFIED)
au = mod(modification_type="unilateral", signed_parties=["GOV"])
check("8.5 authorized unilateral: type satisfied", au["type_check"]["result"], REG.SATISFIED)
unauth = mod(officer_authority_current=False)
check("8.5 an unauthorized person fails the authority rule",
      unauth["authority_check"]["result"], REG.NOT_SATISFIED)
noauth_ev = mod(authority_evidence=None)
check("8.5 missing authority evidence is INSUFFICIENT_EVIDENCE",
      noauth_ev["authority_check"]["result"], REG.INSUFFICIENT_EVIDENCE)
# SIGNATURES ARE NOT AUTHORITY
sig_only = mod(authority_evidence=None, signed_parties=["GOV", "CTR", "WITNESS"])
check("8.5 signatures alone are never authority",
      sig_only["authority_check"]["result"], REG.INSUFFICIENT_EVIDENCE)
noform = mod(written_instrument=None)
check("8.5 an applicable SF30 that is absent is not satisfied",
      noform["form_check"]["result"], REG.NOT_SATISFIED)
bad_bilateral = mod(modification_type="bilateral", signed_parties=["GOV"])
check("8.5 a bilateral modification signed by one party is not satisfied",
      bad_bilateral["type_check"]["result"], REG.NOT_SATISFIED)
notype = mod(modification_type=None)
check("8.5 an unstated unilateral/bilateral distinction is not satisfied",
      notype["type_check"]["result"], REG.INSUFFICIENT_EVIDENCE)
# NO COUNT IS THE RESULT (this module is not Category 4.6)
three = V6.modification_governance({"contract_id": "C1", "modifications": [
    {"modification_id": f"M{i}", "federal_context": True, "modification_type": "bilateral",
     "executing_official": "CO", "authority_evidence": "warrant", "signed_parties": ["G", "C"],
     "sf30_applicable": True, "written_instrument": "SF30", "reviewer": "co"} for i in range(3)]})
check("8.5 the result carries no modification-frequency figure",
      any(k in three for k in ("modification_count", "frequency", "rate")), False)
check("8.5 every modification is assessed individually", len(three["modification_results"]), 3)

# =============================================================================================
# 8.6 QUALITY COMPLIANCE. Contract: 100 applicable assessed, 92 satisfied -> 0.92.
# =============================================================================================
reqs100 = [{"requirement_id": f"Q{i}", "applicable": True, "assessed": True,
            "satisfied": i < 92, "criticality": "medium", "source": "SPEC-1"}
           for i in range(100)]
q = V6.quality_compliance({"register_id": "QR-1", "requirements": reqs100})
check("8.6 92 of 100 satisfied", q["quality_compliance_rate"], 0.92)
check("8.6 the denominator is applicable assessed", q["applicable_assessed"], 100)
# UNASSESSED DO NOT COUNT AS SATISFIED (fault 47)
mixed = V6.quality_compliance({"requirements": [
    {"requirement_id": "Q1", "applicable": True, "assessed": True, "satisfied": True},
    {"requirement_id": "Q2", "applicable": True, "assessed": False, "satisfied": None}]})
check("8.6 unassessed requirements leave the denominator", mixed["applicable_assessed"], 1)
check("8.6 unassessed requirements are not satisfied", mixed["unassessed_applicable"], ["Q2"])
check("8.6 unassessed requirements do not make the rate 1.0 by inclusion",
      mixed["quality_compliance_rate"], 1.0)
# ONE CRITICAL EXCEPTION SURVIVES A 99% AGGREGATE (fault 46)
crit99 = [{"requirement_id": f"Q{i}", "applicable": True, "assessed": True, "satisfied": True}
          for i in range(99)] + [
    {"requirement_id": "QCRIT", "applicable": True, "assessed": True, "satisfied": False,
     "criticality": "critical", "source": "SPEC-9", "corrective_action": "open"}]
c99 = V6.quality_compliance({"requirements": crit99})
check("8.6 the aggregate is 0.99", c99["quality_compliance_rate"], 0.99)
check("8.6 the one critical exception is separately visible", len(c99["critical_exceptions"]), 1)
check("8.6 the critical exception is named", c99["critical_exceptions"][0]["requirement_id"],
      "QCRIT")
# no assessed applicable requirements -> abstain, never a fabricated denominator (fault 48)
none_assessed = V6.quality_compliance({"requirements": [
    {"requirement_id": "Q1", "applicable": True, "assessed": False}]})
check("8.6 no assessed applicable requirement abstains",
      none_assessed["disposition"], "NOT_ESTIMABLE")
check("8.6 no rate is estimated", none_assessed["quality_compliance_rate"], None)
try:
    V6.quality_compliance({"requirements": []})
    check("8.6 an empty register abstains", "no raise", "StructureAbsent")
except StructureAbsent:
    check("8.6 an empty register abstains", "StructureAbsent", "StructureAbsent")

# =============================================================================================
# 8.7 SAFETY PERFORMANCE. Contract: 3 cases / 200000 hours -> 3.0; 0 hours -> abstain.
# =============================================================================================
s = V6.safety_performance({"recordable_cases": 3, "employee_hours_worked": 200000,
                           "reporting_period": "2026-07"})
check("8.7 incidence rate 3 * 200000 / 200000", s["incidence_rate"], 3.0)
check("8.7 the OSHA identity is the rule cited", s["rule"]["rule_id"], "OSHA-INCIDENCE-RATE")
zero = V6.safety_performance({"recordable_cases": 3, "employee_hours_worked": 0})
check("8.7 zero hours is an invalid denominator", zero["lagging_disposition"],
      "INVALID_DENOMINATOR")
check("8.7 zero hours returns no finite rate", zero["incidence_rate"], None)
nohours = V6.safety_performance({"recordable_cases": 3})
check("8.7 absent hours abstains rather than fabricating exposure",
      nohours["lagging_disposition"], "ABSTAIN_NO_EXPOSURE_DATA")
check("8.7 absent hours produces no rate", nohours["incidence_rate"], None)
# ZERO RECORDABLES ALONE IS NEVER A FAVOURABLE SYSTEM CLAIM (fault 51)
zr = V6.safety_performance({"recordable_cases": 0, "employee_hours_worked": 100000})
check("8.7 zero recordables yields a rate of zero", zr["incidence_rate"], 0.0)
check("8.7 zero recordables makes no system claim", zr["system_claim"], None)
check("8.7 no 'strong safety system' wording appears", "strong safety" in str(zr).lower(), False)
# leading and lagging are never averaged
lead = V6.safety_performance({"recordable_cases": 1, "employee_hours_worked": 100000,
                              "leading_indicators": [{"indicator": "training_completion",
                                                      "value": 0.95, "period": "2026-07"}]})
check("8.7 leading evidence is recorded", lead["leading_disposition"], "RECORDED")
check("8.7 no combined index is produced", lead["combined_index"], None)
# a meeting-minute mention is not a numerator (fault 49)
mm = V6.safety_performance({"safetyIncidentsDiscussed": 4, "employee_hours_worked": 200000})
check("8.7 a meeting-minute mention is not an incidence numerator",
      mm["incidence_rate"], None)
# severe events remain visible
sev = V6.safety_performance({"recordable_cases": 0, "employee_hours_worked": 100000,
                             "severe_events": [{"event": "high-potential near miss"}]})
check("8.7 severe events remain visible", len(sev["severe_events"]), 1)

# =============================================================================================
# 8.8 ENVIRONMENTAL COMPLIANCE.
# =============================================================================================
def env(**kw):
    base = {"site_id": "S1", "jurisdiction": "State of Alaska",
            "permitting_authority": "STATE", "permit_id": "AKR10",
            "requirements": [{"requirement_id": "E1", "applicable": True, "assessed": True,
                              "satisfied": True}]}
    base.update(kw)
    return V6.environmental_compliance(base)


e = env(requirements=[{"requirement_id": f"E{i}", "applicable": True, "assessed": True,
                       "satisfied": i < 9} for i in range(10)])
check("8.8 9 of 10 satisfied", e["environmental_compliance_rate"], 0.9)
# EPA IS NOT ASSUMED (fault 52)
st = env()
check("8.8 a state-permitted site does not cite the EPA CGP", st["rule"], None)
epa = env(permitting_authority="EPA")
check("8.8 an EPA-permitted site cites the EPA CGP", epa["rule"]["rule_id"],
      "EPA-CGP-2022-MODIFIED")
noauth_e = env(permitting_authority=None)
check("8.8 an unestablished permitting authority is not assessed",
      noauth_e["disposition"], "APPLICABILITY_NOT_ESTABLISHED")
check("8.8 an unestablished authority produces no rate",
      noauth_e["environmental_compliance_rate"], None)
# unassessed do not count as satisfied (fault 53)
un = env(requirements=[{"requirement_id": "E1", "applicable": True, "assessed": True,
                        "satisfied": True},
                       {"requirement_id": "E2", "applicable": True, "assessed": False}])
check("8.8 unassessed requirements leave the denominator", un["applicable_assessed"], 1)
check("8.8 unassessed requirements are listed", un["unassessed_applicable"], ["E2"])
# critical permit violation is noncompensatory (fault 54)
cv = env(requirements=[{"requirement_id": f"E{i}", "applicable": True, "assessed": True,
                        "satisfied": True} for i in range(99)] + [
    {"requirement_id": "ECRIT", "applicable": True, "assessed": True, "satisfied": False,
     "criticality": "critical", "source": "PERMIT"}])
check("8.8 the aggregate is 0.99", cv["environmental_compliance_rate"], 0.99)
check("8.8 the critical violation stays separately visible", len(cv["critical_violations"]), 1)
# a meeting-minute issue count is not a compliance percentage (fault 55)
mmi = V6.environmental_compliance({"site_id": "S", "jurisdiction": "AK",
                                   "permitting_authority": "STATE",
                                   "environmentalIssuesDiscussed": 3})
check("8.8 a meeting-minute issue count yields no compliance rate",
      mmi["environmental_compliance_rate"], None)
check("8.8 a meeting-minute issue count abstains", mmi["disposition"], "NOT_ESTIMABLE")

# =============================================================================================
# 8.9 CONTRACTOR PERFORMANCE ASSESSMENT SIGNAL.
# =============================================================================================
ORDER = ["Unsatisfactory", "Marginal", "Satisfactory", "Very Good", "Exceptional"]
cp = V6.contractor_assessment({
    "source_system": "CPARS", "assessment_id": "CPARS-SYNTH-1", "contract_id": "C1",
    "assessment_period": "2026", "status": "interim", "rating_order": ORDER,
    "factor_definitions_version": "2026", "reviewer": "assessing official",
    "narratives": {"Quality": "synthetic narrative"},
    "contractor_comments_state": "submitted", "agency_review_state": "under review",
    "data_origin": "SYNTHETIC_RESEARCH_FIXTURE",
    "factor_ratings": [{"factor": "Quality", "rating": "Very Good", "narrative": "n1"},
                       {"factor": "Schedule", "rating": "Marginal", "narrative": "n2",
                        "critical": True}]})
check("8.9 a CPARS record with an assessment id is official", cp["is_official_cpars_record"], True)
check("8.9 the worst factor is preserved separately", cp["worst_factor"]["factor"], "Schedule")
check("8.9 no aggregate rating is produced", cp["aggregate"], None)
check("8.9 the narratives survive", cp["narratives"], {"Quality": "synthetic narrative"})
check("8.9 the agency review state survives", cp["agency_review_state"], "under review")
check("8.9 the contractor comment state survives", cp["contractor_comments_state"], "submitted")
# AN INTERNAL SCORE CAN NEVER BE LABELLED CPARS (fault 56)
internal = V6.contractor_assessment({
    "source_system": "INTERNAL_PROJECT_RUBRIC", "assessment_id": "INT-1", "rating_order": ORDER,
    "factor_ratings": [{"factor": "Quality", "rating": "Satisfactory"}]})
check("8.9 an internal source is not a CPARS record",
      internal["is_official_cpars_record"], False)
check("8.9 an internal source is labelled internal", internal["label"],
      "internal Contractor Performance Assessment Signal")
check("8.9 an internal record never carries the CPARS label",
      "CPARS" in internal["label"], False)
# missing governed assessment abstains
check("8.9 no governed assessment abstains",
      V6.contractor_assessment({"source_system": "CPARS", "assessment_id": "X"})["disposition"],
      "ABSTAIN_NO_GOVERNED_ASSESSMENT")

# =============================================================================================
# 8.1 ABM. HAND-COMPUTED EVENT TRACE (section 45: computed BEFORE production ran).
#
#   t=0  PM receives the qualified HIGH_IMPACT adverse signal            SIGNAL_RECEIVED
#   t=0  PM recognises final authority required = OWNER                  AUTHORITY_RECOGNISED
#   t=0  PM sends a response request to CONTRACTOR (latency 2 -> t=2)    RESPONSE_REQUEST_SENT
#        ... no final authorization exists at t=0 or t=1 ...
#   t=2  CONTRACTOR response becomes available to PM                     RESPONSE_AVAILABLE
#   t=2  CONTRACTOR is confirmed unable to authorize                     AUTHORIZATION_NOT_PERMITTED
#   t=2  PM escalates the governed recommendation package to OWNER       ESCALATED_TO_OWNER
#        (owner latency 1 -> delivery t=3)
#   t=3  OWNER processes the package and authorizes                      AUTHORIZED
#   terminal: AUTHORIZED_BY_OWNER at t=3
# =============================================================================================
def abm_structure(**kw):
    base = {
        "agents": [{"agent_id": "OWN-1", "role": "OWNER", "response_latency": 1},
                   {"agent_id": "PM-1", "role": "PROJECT_MANAGER", "response_latency": 0},
                   {"agent_id": "CTR-1", "role": "CONTRACTOR", "response_latency": 2}],
        "authority_matrix": [{"action_class": "HIGH_IMPACT",
                              "permitted_recommender": "PROJECT_MANAGER",
                              "required_approver": "OWNER",
                              "contractor_response_required": True,
                              "procedural_requirement": "governed procedural review",
                              "evidence_requirement": "qualified_signal"}],
        "action_class": "HIGH_IMPACT", "owner_decision": "AUTHORIZE"}
    base.update(kw)
    return base


def abm_run(structure, eligible=True, abstaining=False):
    m = model_from(structure, signal_eligible=eligible, signal_abstaining=abstaining)
    terminal = m.run()
    return terminal, [(h["t"], h["actor"], h["event"]) for h in m.history], m


EXPECTED_TRACE = [
    (0, "PM-1", "SIGNAL_RECEIVED"),
    (0, "PM-1", "AUTHORITY_RECOGNISED"),
    (0, "PM-1", "RESPONSE_REQUEST_SENT"),
    (2, "CTR-1", "RESPONSE_AVAILABLE"),
    (2, "CTR-1", "AUTHORIZATION_NOT_PERMITTED"),
    (2, "PM-1", "ESCALATED_TO_OWNER"),
    (3, "OWN-1", "AUTHORIZED"),
]
term, trace, model = abm_run(abm_structure())
check("8.1 terminal state is AUTHORIZED_BY_OWNER", term, AUTHORIZED_BY_OWNER)
check("8.1 terminal time is t=3", model.env.clock, 3)
check("8.1 the hand-computed event trace matches transition for transition",
      trace, EXPECTED_TRACE)
check("8.1 the audit history records every state transition", len(model.history), 7)
# PERTURBATION ORACLE: contractor latency 2 -> 4 (fault 34)
pert = abm_structure()
pert["agents"][2]["response_latency"] = 4
term4, trace4, model4 = abm_run(pert)
check("8.1 perturbation keeps the same authority semantics", term4, AUTHORIZED_BY_OWNER)
check("8.1 perturbation shifts terminal authorization to t=5", model4.env.clock, 5)
check("8.1 perturbation changes the event timeline", trace4 != trace, True)
check("8.1 owner authorization cannot precede the contractor response",
      [t for t, a, e in trace4 if e == "AUTHORIZED"][0] >
      [t for t, a, e in trace4 if e == "RESPONSE_AVAILABLE"][0], True)
# evidence insufficient -> no fabricated authorization (fault 33)
term_ev, _, _ = abm_run(abm_structure(evidence_sufficient=False))
check("8.1 insufficient evidence does not auto-authorize", term_ev != AUTHORIZED_BY_OWNER, True)
check("8.1 insufficient evidence requests evidence or defers",
      term_ev in (REQUEST_EVIDENCE, DEFERRED), True)
# owner unavailable -> defer; PM cannot self-upgrade
term_ou, trace_ou, _ = abm_run(abm_structure(owner_available=False))
check("8.1 an unavailable owner defers", term_ou, DEFERRED)
check("8.1 the PM does not self-upgrade authority",
      any(e == "AUTHORIZED" for _, _, e in trace_ou), False)
# contractor attempts owner-only authorization -> rejected (fault 31)
matrix_ctr = abm_structure()
matrix_ctr["authority_matrix"][0]["required_approver"] = "OWNER"
_, trace_ctr, _ = abm_run(matrix_ctr)
check("8.1 the contractor is recorded as unable to authorize",
      any(e == "AUTHORIZATION_NOT_PERMITTED" and a == "CTR-1" for _, a, e in trace_ctr), True)
# procedural review incomplete -> cannot finalize
term_p, _, _ = abm_run(abm_structure(procedural_review_complete=False))
check("8.1 an incomplete procedural review cannot finalize", term_p,
      BLOCKED_PROCEDURE_INCOMPLETE)
# abstaining signal -> no fabricated state (fault 8)
term_a, _, _ = abm_run(abm_structure(), abstaining=True)
check("8.1 an abstaining signal produces no adverse or favourable state", term_a,
      NO_ACTION_ABSTAINING_SIGNAL)
# unqualified signal never reaches an agent (fault 3)
term_u, trace_u, _ = abm_run(abm_structure(), eligible=False)
check("8.1 an unqualified signal blocks the governed action", term_u,
      BLOCKED_UNQUALIFIED_EVIDENCE)
check("8.1 an unqualified signal authorizes nothing",
      any(e == "AUTHORIZED" for _, _, e in trace_u), False)
# structural guards (faults 29, 30)
from app.simulation.abm import ABMStructureError                     # noqa: E402
try:
    abm_run(abm_structure(agents=[]))
    check("8.1 no agents fails the structural guard", "no raise", "ABMStructureError")
except ABMStructureError:
    check("8.1 no agents fails the structural guard", "ABMStructureError", "ABMStructureError")
try:
    abm_run(abm_structure(authority_matrix=[]))
    check("8.1 no authority matrix fails the structural guard", "no raise", "ABMStructureError")
except ABMStructureError:
    check("8.1 no authority matrix fails the structural guard", "ABMStructureError",
          "ABMStructureError")
# stochastic latency is never introduced
check("8.1 latency is deterministic and declared",
      V6.abm_governance(abm_structure(), signal_eligible=True,
                        signal_abstaining=False)["stochastic_latency"], False)
# no Bayesian layer
import app.simulation.abm as _abm_mod                                # noqa: E402
_abm_names = dir(_abm_mod)
check("8.1 no Bayesian construct is exported by the model",
      [n for n in _abm_names
       if any(w in n.lower() for w in ("prior", "posterior", "likelihood", "bayes"))], [])
check("8.1 the model draws no random number",
      any(w in open(_abm_mod.__file__).read() for w in ("import random", "rand(")), False)

# =============================================================================================
# WORDING GUARD (section 42): no current Category-8 production string makes a legal claim.
# =============================================================================================
STRINGS = []
for r in (caseA, caseB, caseC, caseD, a11, ontime, lateR, incomp, naR, unres, q, c99, s, zr,
          e, st, epa, cp, internal, ab, unauth):
    STRINGS.append(str(r))
bad = []
for text in STRINGS:
    bad.extend(REG.prohibited_claims_in(text))
check("wording guard: no prohibited legal-compliance claim in any Category-8 result", bad, [])
check("wording guard: the permitted conformance form of words is used",
      "subject to responsible-authority review" in caseA["statement"], True)

# =============================================================================================
# RUN 31 PASS 1: THE THREE CLOSED DEFECTS, ASSERTED THROUGH THE PRODUCTION DISPATCHER.
# =============================================================================================
from app.simulation import registry as _REG                          # noqa: E402


def _prod(mid, si):
    return _REG.run_module(mid, si, lambda: 0.5, "2026-07-31")


# --- 2A: a real Quality Audit must not be refused for want of a meeting-minute mention --------
_q = _prod("A6.1", {"qualityAuditScore": 92, "totalFindings": 18, "criticalFindings": 1})
check("2A a Quality Audit with NO meeting-minute deficiency field is not refused for that reason",
      _q.get("canonical_disposition"), "CANONICAL_RESULT")
check("2A and the real extracted evidence is preserved on the row",
      _q.get("recorded_audit_evidence"),
      {"quality_audit_score": 92, "total_findings": 18, "critical_findings": 1})
check("2A and no compliance rate is fabricated from a summary",
      _q.get("quality_compliance_rate"), None)
check("2A and the disposition says why", _q.get("disposition"), "NOT_ESTIMABLE")
check("2A the old meeting-minute prerequisite appears nowhere in the result",
      "qualityDeficienciesNoted" in str(_q), False)
# and a project with NOTHING still abstains, so the fix did not make the module credulous
check("2A a project with no quality evidence at all still abstains",
      _prod("A6.1", {}).get("insufficient_data"), True)

# --- 2B: safety, wired only after the upstream identity was proved by execution ----------------
_s = _prod("A6.2", {"oshaRecordableIncidents": 3, "totalManhours": 200000})
check("2B the production path computes the OSHA identity from the corpus fields",
      _s.get("incidence_rate"), 3.0)
check("2B 7 cases over 350,000 hours is 4.0 through the production path",
      _prod("A6.2", {"oshaRecordableIncidents": 7,
                     "totalManhours": 350000}).get("incidence_rate"), 4.0)
# THE DOCUMENT-STATED RATE NEVER WINS. Executing extraction_merge proved a stated rate is emitted
# as-is and is never checked against the identity, so the canonical module recomputes it.
_stated = _prod("A6.2", {"oshaRecordableIncidents": 3, "totalManhours": 200000,
                         "oshaIncidentRate": 99.9})
check("2B a document-stated rate does not override the computed identity",
      _stated.get("incidence_rate"), 3.0)
check("2B zero hours abstains rather than returning a finite rate",
      _prod("A6.2", {"oshaRecordableIncidents": 3, "totalManhours": 0}).get("incidence_rate"),
      None)
check("2B zero hours names the invalid denominator",
      _prod("A6.2", {"oshaRecordableIncidents": 3,
                     "totalManhours": 0}).get("lagging_disposition"), "INVALID_DENOMINATOR")
check("2B meeting-minute mentions alone produce no rate",
      _prod("A6.2", {"safetyIncidentsDiscussed": 4}).get("incidence_rate"), None)
check("2B hours are never fabricated when only cases are recorded",
      _prod("A6.2", {"oshaRecordableIncidents": 3}).get("incidence_rate"), None)

# --- 2C: FAR 43.301 -- a rule may not require as prerequisite the condition it tests -----------
def _form(**kw):
    base = {"modification_id": "M1", "federal_context": True, "modification_type": "bilateral",
            "executing_official": "CO", "authority_evidence": "warrant",
            "signed_parties": ["G", "C"], "sf30_applicable": True,
            "written_instrument": "SF30", "reviewer": "co"}
    base.update(kw)
    return V6.modification_governance({"modifications": [base]}
                                      )["modification_results"][0]["form_check"]["result"]


check("2C applicable + SF30 present", _form(), REG.SATISFIED)
check("2C applicable + SF30 ABSENT is NOT_SATISFIED, not INSUFFICIENT_EVIDENCE",
      _form(written_instrument=None), REG.NOT_SATISFIED)
check("2C applicability unknown is INSUFFICIENT_EVIDENCE",
      _form(sf30_applicable=None), REG.INSUFFICIENT_EVIDENCE)
check("2C the evidence establishing applicability is still required",
      "sf30_applicable" in REG.FAR_43_301.required_evidence, True)
check("2C but the tested condition is NOT a prerequisite for evaluating the rule",
      "written_instrument" in REG.FAR_43_301.required_evidence, False)

# --- lineage: the three removed declarations derive UNRESOLVED, never independent --------------
from app.simulation.lineage import lineage_status                    # noqa: E402
for _m in ("B3.2", "B3.4", "B3.5"):
    check(f"lineage {_m} derives UNRESOLVED from the removed declaration",
          lineage_status(_m, applicable=True), "LINEAGE_UNRESOLVED")
from app.simulation.qualified_evidence import ELIGIBLE_STATES        # noqa: E402
from app.simulation.models_cat89 import _qualify                     # noqa: E402
check("lineage UNRESOLVED is never treated as independent",
      _qualify("B3.2", {"evidence_id": "x"}).independence_established, False)

print()
for f in FAILURES:
    print("FAIL:", f)
print(f"RESULT: {PASS}/{PASS + FAIL} checks passed")
sys.exit(1 if FAIL else 0)
