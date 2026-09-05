"""
RUN 31 PASS 2 ACCEPTANCE. Every assertion here goes through the REAL production dispatcher.

Nothing calls a qualification helper directly to prove the boundary: section 13 forbids it and
Run 30's defect is what it forbids. The gated set is read from the boundary's own derivation
against the shipped registry CSV, so this file contains no hand-written route list.
"""
# Run 137, Item 1: a removed module identifier is SUBSTITUTED, not dispatched.
import os as _r96_os, sys as _r96_sys  # noqa: E402
_r96_sys.path.insert(0, _r96_os.path.dirname(_r96_os.path.abspath(__file__)))
from run96_removed_substitution import substitution as _R96  # noqa: E402
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation import registry as REG                                # noqa: E402
from app.simulation.lineage import independence_established, lineage_status  # noqa: E402
from app.simulation.models import SIMULATION_VERSION, VALIDATED           # noqa: E402
from app.simulation.models_cat89 import CAT89_CANONICAL                   # noqa: E402
from app.simulation.qualification_boundary import (                       # noqa: E402
    gate_installed_for, gated_module_ids)
from app.simulation import canonical_v6 as V6                             # noqa: E402

P = F = 0
FAILS = []


def check(ok, label, detail=""):
    global P, F
    if ok:
        P += 1
        print(f"  PASS  {label}")
    else:
        F += 1
        FAILS.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def head(t):
    print("\n" + "=" * 78 + f"\n{t}\n" + "=" * 78)


NOOP = (lambda: 0.5)
CUT = "2026-06-30"
SI = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
      "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
      "actualPctComplete": 40.0, "plannedPctComplete": 45.0}
UNQ = {"qualification_state": "UNASSESSED"}
QUAL = {"qualification_state": "QUALIFIED", "timeliness_status": "TIMELY",
        "verification_status": "verified", "source_authority": "system_of_record"}
REFUSED = "evidence_not_qualified_for_use"


def run(mid, si):
    return _R96.dispatch(REG.run_module, globals(), mid, dict(si), NOOP, CUT)


head("1. RAW BYPASS = 0 THROUGH THE REAL DISPATCHER, ROUTES DERIVED FROM THE REGISTRY")
# THE EXPECTED GATED POPULATION IS ASSERTED FIRST, AND THIS IS NOT DECORATION. Iterating
# `gated_module_ids()` alone is SELF-LIMITING: if a consumer category were dropped from the gated
# set, its modules would simply leave the loop and every remaining check would still pass. The
# Pass-2 fault campaign found exactly that vacuity in this guard -- removing Signal Synthesis and
# Evidence Combination from GATED_CATEGORY_NAMES left it green.
#
# So the population is derived INDEPENDENTLY from the shipped registry CSV -- every module in the
# four consumer categories the architecture names -- and the gated set must equal it exactly.
import csv as _csv                                                        # noqa: E402
_CSV = pathlib.Path(REG.CSV_PATH)
with _CSV.open(encoding="utf-8-sig", newline="") as _fh:
    _reg = list(_csv.DictReader(_fh))
CONSUMER_CATEGORIES = {"Signal Synthesis", "Evidence Combination",
                       "Regulatory & Authority Thresholds", "Delivery Quality Performance",
                       "Decision Optimization"}
EXPECTED_GATED = {r["new_id"] for r in _reg if r["category_name"] in CONSUMER_CATEGORIES}
from app.simulation.qualification_contract import (                    # noqa: E402
    CONFIGURATION_MISSING, NOT_APPLICABLE, REQUIRED, expected_not_applicable,
    expected_qualification_required, requirement_for)
gated = gated_module_ids()
# THE GOVERNED CONTRACT, asserted against the independently derived expectation.
check(set(gated) == expected_qualification_required(),
      "the gated set equals the governed contract's REQUIRED population",
      f"diff={sorted(set(gated) ^ expected_qualification_required())}")
check(not (set(gated) & expected_not_applicable()),
      "and no Category-9 route is gated behind its own output",
      str(sorted(set(gated) & expected_not_applicable())))
check(all(requirement_for(m) == REQUIRED for m in expected_qualification_required()),
      "every expected consumer route carries a REQUIRED declaration")
check(requirement_for("NO.SUCH.MODULE") == CONFIGURATION_MISSING,
      "and an undeclared route resolves to CONFIGURATION_MISSING, so the default branch is deny")
check(set(gated) == EXPECTED_GATED,
      f"the gated population is exactly the {len(EXPECTED_GATED)} modules in the four consumer "
      f"categories, derived independently from the registry CSV",
      f"missing={sorted(EXPECTED_GATED - set(gated))} extra={sorted(set(gated) - EXPECTED_GATED)}")
for _cat in sorted(CONSUMER_CATEGORIES):
    _want = {r["new_id"] for r in _reg if r["category_name"] == _cat}
    _have = {m for m, c in gated.items() if c == _cat}
    check(_have == _want, f"{_cat}: all {len(_want)} modules are gated",
          f"ungated={sorted(_want - _have)}")
by_cat = {}
for mid, cat in sorted(gated.items()):
    r = run(mid, dict(SI, evidenceQualification=UNQ))
    disabled = r.get("activation_state") in ("DISABLED_UNSAFE", "DISABLED_EVIDENCE_UNDER_REVIEW")
    ok = r.get("abstention_reason_code") == REFUSED or disabled
    by_cat.setdefault(cat, []).append((mid, ok))
    if not ok:
        check(False, f"{cat} {mid}: raw unassessed evidence was consumed", str(r)[:120])
for cat, rows in sorted(by_cat.items()):
    bad = [m for m, ok in rows if not ok]
    check(not bad, f"{cat}: raw bypass = 0 across {len(rows)} production routes", str(bad))
check(all(gate_installed_for(VALIDATED[m][1]) for m in gated),
      f"the boundary is installed on all {len(gated)} gated dispatch entries")
check(not any(gate_installed_for(VALIDATED[m][1]) for m in CAT89_CANONICAL if m.startswith("C1.")),
      "and on none of the seven Category-9 entries, which perform the assessment")

head("1b. MISSING-ASSESSMENT BYPASS = 0 (owner closure: absence fails closed)")
_miss = {}
for mid, cat in sorted(gated.items()):
    r = _R96.dispatch(REG.run_module, globals(), mid, dict(SI), NOOP, CUT)          # NO assessment supplied at all
    disabled = r.get("activation_state") in ("DISABLED_UNSAFE",
                                             "DISABLED_EVIDENCE_UNDER_REVIEW")
    ok = r.get("abstention_reason_code") == "CATEGORY9_ASSESSMENT_MISSING" or disabled
    _miss.setdefault(cat, []).append((mid, ok))
for cat, rws in sorted(_miss.items()):
    bad = [m for m, ok in rws if not ok]
    check(not bad, f"{cat}: missing-assessment bypass = 0 across {len(rws)} routes", str(bad))
_probe = _R96.dispatch(REG.run_module, globals(), "B4.3", dict(SI), NOOP, CUT)
_pq = _probe.get("qualification") or {}
check(_probe.get("consumer_executed") is False
      and _pq.get("qualification_state") == "UNASSESSED"
      and _pq.get("qualification_reason") == "CATEGORY9_ASSESSMENT_MISSING"
      and _probe.get("simulation_version") and _probe.get("lineage"),
      "and the blocked row carries module, UNASSESSED, the reason, lineage SEPARATELY, the "
      "simulation version and consumer_executed=false", str(_pq))
check(_pq.get("qualification_state") != "QUALIFIED",
      "and never stamps QUALIFIED after refusing")

head("2. QUALIFICATION PRECEDENCE: NOTHING MISSING BECOMES FAVOURABLE")
cases = [
    ("missing evidence != 0", {"required_inputs": ["cpi"], "critical_missing": ["cpi"]}),
    ("unknown != Green", {"qualification_state": "UNASSESSED"}),
    ("UNASSESSED != QUALIFIED", {"qualification_state": "UNASSESSED"}),
    ("material conflict != averaged away",
     {"material_conflicts": [{"fact_id": "BAC", "reference_value": 100.0, "value": 110.0}]}),
    ("future-dated != timely", {"timeliness_status": "FUTURE_DATED"}),
]
for label, decl in cases:
    r = run("B4.3", dict(SI, evidenceQualification=decl))
    check(r.get("status_color") is None and r.get("abstention_reason_code") == REFUSED,
          f"precedence: {label}", f"band={r.get('status_color')} code={r.get('abstention_reason_code')}")
# RESTATED BY RUN 32, and the property is preserved rather than dropped. Run 31 proved "the gate
# changes eligibility, not availability" by asserting that qualified evidence still produced a
# BAND. At v20 a Category-10 row carries NO status_color by design -- a decision result is not an
# observation about the project and never enters fusion or voting -- so band presence can no
# longer be the usability signal for any Category-10 module. The gate property is proved by
# EXECUTION instead, which is stronger: with the governed structure supplied through the REAL
# intake, the qualified package reaches the consumer and the consumer computes.
from app import project_data as _pd32  # noqa: E402

_DOC32 = {"projectData": {"constraintSatisfactionProblem": [{
    "effective_period": 1, "supplied_by": "run31 pass-2 acceptance",
    "source": "run32 governed decision structure", "at": "2026-08-17T00:00:00Z",
    "record": {
        "context_id": "PASS2-CSP", "source": "run32 governed decision structure",
        "variables": [{"variable_id": "X", "domain": ["A", "B"]},
                      {"variable_id": "Y", "domain": [1, 2]}],
        "constraints": [{"constraint_id": "c1", "type": "implication",
                         "if": {"X": "A"}, "then": {"Y": 2}}],
    },
}]}}
_qsi = dict(SI, evidenceQualification=QUAL)
_pd32.apply_to_signal_inputs(_qsi, _DOC32, 6)
_q = run("B4.3", _qsi)
check(_q.get("canonical_disposition") == "CANONICAL_RESULT"
      and _q.get("abstention_reason_code") != REFUSED
      and _q.get("status_color") is None,
      "and QUALIFIED evidence still produces the reading, so the gate changes eligibility "
      "rather than disabling the consumer")

head("3. QUALIFICATION AND LINEAGE ARE SEPARATE, IN BOTH DIRECTIONS")
from app.simulation.qualified_evidence import ELIGIBLE_STATES          # noqa: E402
# DIRECTION 1: eligible for its use, and STILL not independently combinable. B4.3's declared
# lineage is ESTABLISHED_DEPENDENT -- it is a transform of the earned-value body -- so
# independence is false for a reason that has nothing to do with its qualification passing.
r = run("B4.3", dict(SI, evidenceQualification=QUAL))
q = r.get("qualification", {})
check(q.get("qualification_state") in ELIGIBLE_STATES and q.get("eligible_for_use") is True,
      "a record can pass qualification for its use ...", str(q))
check(q.get("independence_established") is False,
      "... and still NOT be independently combinable: qualification is not independence",
      str(q.get("lineage_status")))
# DIRECTION 2: an UNRESOLVED-lineage module whose qualification also passes stays non-independent.
r2 = run("B3.2", dict(SI, evidenceQualification=QUAL))
q2 = r2.get("qualification", {})
check(q2.get("lineage_status") == "LINEAGE_UNRESOLVED"
      and q2.get("independence_established") is False,
      "and an UNRESOLVED-lineage module is never independent however its qualification resolves",
      str(q2))
unresolved_independent = [m for m in gated
                          if independence_established(lineage_status(m, applicable=True))
                          and lineage_status(m, applicable=True) == "LINEAGE_UNRESOLVED"]
check(not unresolved_independent, "UNRESOLVED treated independent = 0", str(unresolved_independent))

head("4. CATEGORY 9 IS NOT A VOTE")
check(sorted(REG.CORE_VOTING_MODULES) == ["A1.7", "A1.8"],
      "voting is exactly 2 and both are Category 1", str(sorted(REG.CORE_VOTING_MODULES)))
c9 = [m for m in VALIDATED if m.startswith("C1.")]
check(not (set(c9) & set(REG.CORE_VOTING_MODULES)),
      "no Category-9 module is in the voting set", str(set(c9) & set(REG.CORE_VOTING_MODULES)))
for mid in c9:
    row = run(mid, dict(SI))
    check(row.get("voting_eligible") is False and row.get("category_9_metadata_only") is True,
          f"{mid} row declares itself metadata-only and non-voting")
    check(row.get("status_color") is None,
          f"{mid} asserts no band, so it cannot be read as a project condition")

head("5. 9.1 vs 9.5 AND 9.2 vs 9.7 REMAIN DISTINCT")
nr = V6.nonredundancy(
    {"package_id": "PKG", "components": [
        {"component_id": "COST", "required": True, "present": True,
         "mandatory_fields": ["a"], "values": {"a": 1}},
        {"component_id": "SCHEDULE", "required": True, "present": True,
         "mandatory_fields": ["b"], "values": {"b": 2}},
        {"component_id": "SAFETY", "required": True, "present": False, "critical": True,
         "mandatory_fields": ["h"], "values": {}}]},
    {"required_fields": ["a", "b"], "values": {"a": 1, "b": 2}})
check(nr["field_level_missing_fraction"] == 0.0 and nr["package_coverage"] != 1.0,
      "9.1 shows no field-level missingness while 9.5 shows incomplete package coverage",
      str(nr))
check(nr["distinguishable"] is True, "the two measures do not collapse")
FRESH = {"evaluation_date": "2026-08-16", "effective_date": "2026-08-15",
         "freshness_rule": {"allowed_age_days": 30, "boundary": "inclusive"}}
STALE = {"evaluation_date": "2026-08-16", "effective_date": "2026-06-01",
         "freshness_rule": {"allowed_age_days": 30, "boundary": "inclusive"}}
PERIODS = [{"period_id": "P1", "due_date": "2026-01-30"},
           {"period_id": "P2", "due_date": "2026-03-01"},
           {"period_id": "P3", "due_date": "2026-03-31"}]
missed = V6.reporting_frequency({"expected_periods": PERIODS, "report_history": [
    {"period_id": "P1", "received_date": "2026-01-30"},
    {"period_id": "P3", "received_date": "2026-03-31"}]})
perfect = V6.reporting_frequency({"expected_periods": PERIODS, "report_history": [
    {"period_id": p["period_id"], "received_date": p["due_date"]} for p in PERIODS]})
check(V6.data_timeliness(FRESH)["timeliness_status"] == "TIMELY"
      and missed["reporting_coverage"] != 1.0,
      "9.2 can be TIMELY while 9.7 cadence is incomplete")
check(V6.data_timeliness(STALE)["timeliness_status"] == "STALE"
      and perfect["reporting_coverage"] == 1.0,
      "and 9.7 cadence can be complete while 9.2 is STALE for the current-use rule")

head("6. 8.1 THROUGH THE REAL PRODUCTION DISPATCHER")
ABM = {"agents": [{"agent_id": "OWN-1", "role": "OWNER", "response_latency": 1},
                  {"agent_id": "PM-1", "role": "PROJECT_MANAGER", "response_latency": 0},
                  {"agent_id": "CTR-1", "role": "CONTRACTOR", "response_latency": 2}],
       "authority_matrix": [{"action_class": "HIGH_IMPACT",
                             "permitted_recommender": "PROJECT_MANAGER",
                             "required_approver": "OWNER",
                             "contractor_response_required": True,
                             "procedural_requirement": "governed procedural review",
                             "evidence_requirement": "qualified_signal"}],
       "action_class": "HIGH_IMPACT", "owner_decision": "AUTHORIZE",
       "qualification": QUAL}


def abm_run(**over):
    st = dict(ABM)
    st.update(over)
    return run("B3.1", dict(SI, abmGovernanceModel=st, evidenceQualification=QUAL))


r = abm_run()
trace = [(h["t"], h["actor"], h["event"]) for h in r.get("state_history", [])]
check(r.get("terminal_state") == "AUTHORIZED_BY_OWNER" and r.get("final_time") == 3,
      "production 8.1 reaches AUTHORIZED_BY_OWNER at t=3",
      f"{r.get('terminal_state')} t={r.get('final_time')}")
check(trace == [(0, "PM-1", "SIGNAL_RECEIVED"), (0, "PM-1", "AUTHORITY_RECOGNISED"),
                (0, "PM-1", "RESPONSE_REQUEST_SENT"), (2, "CTR-1", "RESPONSE_AVAILABLE"),
                (2, "CTR-1", "AUTHORIZATION_NOT_PERMITTED"), (2, "PM-1", "ESCALATED_TO_OWNER"),
                (3, "OWN-1", "AUTHORIZED")],
      "and the production event trace matches the hand-computed one transition for transition",
      str(trace))
check(len(r.get("agents") or []) == 3, "production created three agents")
pert = dict(ABM)
pert["agents"] = [dict(a, response_latency=4) if a["role"] == "CONTRACTOR" else a
                  for a in ABM["agents"]]
r4 = run("B3.1", dict(SI, abmGovernanceModel=pert, evidenceQualification=QUAL))
check(r4.get("final_time") == 5 and r4.get("terminal_state") == "AUTHORIZED_BY_OWNER",
      "latency 4 shifts terminal authorization to t=5 with the same authority semantics",
      f"t={r4.get('final_time')}")
check(abm_run(evidence_sufficient=False).get("terminal_state") != "AUTHORIZED_BY_OWNER",
      "insufficient evidence cannot auto-authorize")
check(abm_run(procedural_review_complete=False).get("terminal_state")
      == "BLOCKED_PROCEDURE_INCOMPLETE", "an incomplete procedural review cannot finalize")
check(abm_run(owner_available=False).get("terminal_state") == "DEFERRED",
      "an unavailable owner defers; the PM does not self-upgrade authority")
unq = run("B3.1", dict(SI, abmGovernanceModel=dict(ABM, qualification=UNQ),
                       evidenceQualification=UNQ))
check(unq.get("terminal_state") != "AUTHORIZED_BY_OWNER",
      "and unqualified evidence cannot authorize a high-impact action",
      str(unq.get("terminal_state")))

head("7. PASS-1 RESULTS DO NOT REGRESS")
# These check the canonical ARITHMETIC of A6.1/A6.2/A6.3, so under v19 they supply the governed
# assessment their modules now require -- the ordinary declaration a real caller supplies. The
# GATE itself is proved in sections 1 and 2 above, which deliberately supply nothing.
def run(mid, si):                                                    # noqa: F811
    return _R96.dispatch(REG.run_module, globals(), mid, dict(si, evidenceQualification=dict(QUAL)), NOOP, CUT)
s = run("A6.2", {"oshaRecordableIncidents": 3, "totalManhours": 200000})
check(s.get("incidence_rate") == 3.0, "safety 3 cases / 200,000 h = 3.0", str(s.get("incidence_rate")))
s99 = run("A6.2", {"oshaRecordableIncidents": 3, "totalManhours": 200000,
                   "oshaIncidentRate": 99.9})
check(s99.get("incidence_rate") == 3.0
      and s99.get("document_stated_incident_rate") == 99.9
      and s99.get("document_stated_rate_agrees") is False,
      "the document-stated 99.9 is preserved as a labelled claim and does not override 3.0")
check(run("A6.2", {"oshaRecordableIncidents": 3, "totalManhours": 0}).get("lagging_disposition")
      == "INVALID_DENOMINATOR", "zero hours remains INVALID_DENOMINATOR with no rate")
q = run("A6.1", {"qualityAuditScore": 92, "totalFindings": 18, "criticalFindings": 1})
check(q.get("disposition") == "NOT_ESTIMABLE" and q.get("quality_compliance_rate") is None
      and q.get("recorded_audit_evidence"),
      "quality returns NOT_ESTIMABLE with genuine evidence preserved and no fabricated denominator")
e = run("A6.3", {"environmentalComplianceRate": 0.925, "environmentalViolations": 3})
check(e.get("disposition") == "APPLICABILITY_NOT_ESTABLISHED"
      and e.get("environmental_compliance_rate") is None
      and e.get("recorded_environmental_evidence"),
      "environmental applicability precedes conformance, with the real evidence preserved")
check(e.get("rule") is None,
      "and EPA CGP is not assumed to apply where the authority is not established")

head("8. NO UNSUPPORTED LEGAL-COMPLIANCE CLAIM IN CURRENT CATEGORY-8 OUTPUT")
from app.simulation import regulatory as RG                              # noqa: E402
bad = []
for mid in [m for m in CAT89_CANONICAL if not m.startswith("C1.")]:
    txt = str(run(mid, dict(SI, evidenceQualification=QUAL)))
    bad.extend(f"{mid}:{c}" for c in RG.prohibited_claims_in(txt))
check(not bad, "no current Category-8 production output makes a prohibited legal claim", str(bad))

print()
for f in FAILS:
    print("FAIL:", f)
print(f"RESULT: {P}/{P + F} checks passed")
sys.exit(1 if F else 0)
