"""
RUN 19 -- Category 8, governance and compliance. Nine scientific targets, none of which had been
assessed before this run.

THE GOVERNING RULE, from supervisory specification section 17:
    A RULE CHECK IS NOT A LEGAL DETERMINATION.
No module may claim FAR, OMB, OSHA or EPA compliance or any equivalent legal certification. The
permitted form is that available evidence satisfies, does not satisfy, or is insufficient for
the configured rule check, subject to responsible-authority review.

The specification also warns in terms that Category 8 must not be cleared merely because current
code returns a result. Every module here returns a result; that is the starting point of the
assessment, not the end of it.

REGULATORY BASIS. Everything is evaluated against the dated snapshot the committed specification
carries, REGULATORY_SNAPSHOT_2026-08-12. Nothing here is described as current law and no
superseding source is asserted. Where a module would need an authority the snapshot does not
supply, that is recorded as a gap rather than filled.

RUN 20 CYCLE 2 attempted live retrieval of the primary sources for 8.2, 8.3 and 8.4 and could
not obtain any of them: acquisition.gov, the eCFR, whitehouse.gov and two mirror hosts are all
refused at the egress proxy in this container. A general web search returned the substance of
FAR 34.201 and it agrees with the snapshot on every point this category depends on, including
that the section states no numeric cost-overrun threshold, but a search engine summary is not a
primary document and none is claimed to have been read. The snapshot is the authority, and it is
a sufficient one: the four corrections made in cycle 2 all REMOVE unsupported regulatory claims
and none of them introduces a threshold, so no retrieved provision is needed to justify any of
them. A module is therefore no longer recorded REGULATORY_VERSION_BLOCKED merely because live
retrieval failed. That disposition is reserved for a module whose applicable versioned authority
cannot be established even from the snapshot.

Oracles come from run17/oracle/oracles_cat_8.py, self proved at import.
"""

from __future__ import annotations

import datetime
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE / "run17"))
sys.path.insert(0, str(HERE / "run17" / "oracle"))

from audit_harness import (Audit, RESULT_HEADER, write_results,  # noqa: E402
                           oracle_gate)
from run20_production_changes import expected_flag       # noqa: E402
from population import population                                # noqa: E402
from app.simulation import registry as REG                       # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731

KNOWN_DEFECTS = {
    "8.1/agents-exist": "METHOD_LABEL_MISMATCH",
    "8.2/applicability-evidence": "MISSING_CANONICAL_DATA_STRUCTURE",
    "8.3/configured-requirements": "MISSING_CANONICAL_DATA_STRUCTURE",
    "8.3/edition-recorded": "MISSING_CANONICAL_DATA_STRUCTURE",
    "8.4/reporting-evidence": "MISSING_CANONICAL_DATA_STRUCTURE",
    "8.5/authority-evidence": "CORRECT_PROXY_ONLY",
    "8.6/requirement-conformance": "CORRECT_PROXY_ONLY",
    "8.7/incidence-rate-identity": "MISSING_CANONICAL_DATA_STRUCTURE",
    "8.7/leading-indicators": "MISSING_CANONICAL_DATA_STRUCTURE",
    "8.8/permit-identified": "REGULATORY_VERSION_BLOCKED",
    "8.9/official-source": "MISSING_CANONICAL_DATA_STRUCTURE",
}

A = Audit("category 8", KNOWN_DEFECTS)
O = oracle_gate(A, "oracles_cat_8")

SNAPSHOT = "REGULATORY_SNAPSHOT_2026-08-12"


def run(code_id: str, si: dict) -> dict:
    return REG.run_module(code_id, si, RAND, CUTOFF)


def abstained(out: dict) -> bool:
    return bool(out.get("insufficient_data")) or out.get("status_color") is None


def sentence(out: dict) -> str:
    return str(out.get("evidence_metric") or "")


def signals(state="amber"):
    return {"signals": {"cusum": {"status": state}, "evm": {"status": state},
                        "mc": {"status": state}, "doc": {"status": state}}}


def gate() -> None:
    A.check("GATE", "the Category 8 oracle reproduces the specification's worked answers and its "
                    "regulatory snapshot", not O.self_test(), "; ".join(O.self_test()))
    A.check("GATE", "the regulatory basis is the committed dated snapshot and is labelled as "
                    "such rather than as current law", O.SNAPSHOT == SNAPSHOT)
    ids = {t["module_id"] for t in population()}
    for mid in ("8.1", "8.2", "8.3", "8.4", "8.5", "8.6", "8.7", "8.8", "8.9"):
        A.check("GATE", f"{mid} is one of the hundred scientific targets", mid in ids)
    for code in ("B3.1", "B3.2", "B3.3", "B3.4", "B3.5", "A6.1", "A6.2", "A6.3", "A6.4"):
        A.check("GATE", f"{code} is non-voting", code not in REG.CORE_VOTING_MODULES)


def no_prohibited_claim(mid: str, out: dict) -> None:
    """
    The rule that applies to every module in this category, checked on every module.

    This is a `check`, not a `proposition`: no module currently makes a prohibited claim, and if
    one ever starts to, that is a new defect and the suite should go red rather than record it.
    """
    bad = O.says_prohibited(sentence(out))
    A.check(mid, "the sentence shown to a reader makes no legal-compliance certification, which "
                 "is the rule governing the whole category", not bad, str(bad))


# =============================================================================================
# 8.1 ABM GOVERNANCE LAYER -- specification 17, "8.1"
# =============================================================================================

def m_8_1() -> None:
    # This should be deterministic governance: a signal package leads to an action class, which
    # requires an authority, which a high-impact action may never bypass.
    seen = {}
    for state in ("green", "amber", "red"):
        out = run("B3.1", signals(state))
        seen[state] = out
        A.check("8.1", f"a {state} signal package produces an action and a named authority",
                bool(out.get("action")) and bool(out.get("authority")))
        no_prohibited_claim("8.1", out)

    A.proposition(
        "8.1", "8.1/authority-not-bypassed",
        "a high-impact action, the recovery-plan review and management escalation, never carries "
        "the routine project-level authority: it is escalated to the programme level",
        all("Program director" in str(o.get("authority", ""))
            for o in seen.values()
            if "escalation" in str(o.get("action", "")).lower()))
    A.check("8.1", "the routine action carries the routine authority, so the two paths are "
                   "genuinely distinct rather than one label",
            "Project manager" in str(seen["green"].get("authority", "")))
    A.check("8.1", "invariant: the same signal package always produces the same action and "
                   "authority, so the governance mapping is deterministic rather than sampled",
            len({str(run("B3.1", signals("red"))) for _ in range(5)}) == 1)
    A.proposition(
        "8.1", "8.1/abstains-without-signal-package",
        "with no qualified signal package the module abstains rather than recommending an action",
        abstained(run("B3.1", {})) and abstained(run("B3.1", {"signals": {}})))
    A.check("8.1", "the fairness gate is reported as a state rather than silently absent, and "
                   "its removal is visible on the output",
            "fairness_gate" in seen["red"])
    A.check("8.1", "the fairness gate is always false, because the field that would set it is "
                   "not a signal input and no branch of extraction writes it, so only one "
                   "escalation path exists and a reader is not shown two",
            all(o.get("fairness_gate") is False for o in seen.values()))

    body = (HERE.parent / "app" / "simulation" / "models_decision.py").read_text(encoding="utf-8")
    A.proposition(
        "8.1", "8.1/agents-exist",
        "the module registered as an agent-based governance layer contains agents: entities with "
        "state, behaviour rules and interaction rules",
        any(t in body for t in ("class Agent", "agents =", "agent_state", "behaviour_rule",
                                "interaction")),
        "there is no agent anywhere. The module is a deterministic lookup from a derived health "
        "state to an action sentence, an authority and a documentation requirement. "
        "Specification 8.1 says exactly this: the module should be deterministic governance "
        "rather than agent-based modelling, its preferred identity is an action boundary and "
        "authority matrix, and if the registered name remains an agent-based governance layer "
        "while no agents exist the disposition is a label mismatch. The governance content it "
        "does implement is sound, which is why this is a naming finding and not a defect")


# =============================================================================================
# 8.2 FAR THRESHOLD MONITOR -- specification 17, "8.2"
# =============================================================================================

FAR_IN = {"bac": 1000, "cpi": 0.90, "ev": 400, "ac": 444}


def m_8_2() -> None:
    states = {
        O.evms_applicability(rule_version="FAC 2026-01",
                             acquisition_designation="major_development",
                             contract_clauses=["52.234-4"]),
        O.evms_applicability(rule_version="FAC 2026-01", acquisition_designation="not_major",
                             agency_procedure="does_not_require"),
        O.evms_applicability(rule_version="FAC 2026-01",
                             acquisition_designation="major_development"),
        O.evms_applicability(),
    }
    A.check("8.2", "known-answer: all four applicability states specification 8.2 requires are "
                   "reachable from the deciding evidence",
            states == set(O.APPLICABILITY_STATES), str(sorted(states)))
    A.check("8.2", "known-answer: a project about which the deciding facts are unknown is "
                   "Insufficient Evidence and specifically NOT Not Applicable",
            O.evms_applicability(rule_version="FAC 2026-01") == "Insufficient Evidence")
    A.check("8.2", "the snapshot records that FAR 34.201 establishes applicability through the "
                   "acquisition designation and agency procedure, and does not establish any "
                   "numeric overrun threshold",
            "budget at completion alone"
            in O.AUTHORITIES["FAR_34.201"]["does_not_establish"])

    out = run("B3.2", dict(FAR_IN))
    no_prohibited_claim("8.2", out)
    A.near("8.2", "structure: the declared overrun is the forecast at completion against budget",
           out.get("overrun_pct"), (1000 / 0.90 - 1000) / 1000 * 100, 0.06)
    A.check("8.2", "invariant: the overrun rises monotonically as cost performance falls",
            [run("B3.2", {**FAR_IN, "cpi": c}).get("overrun_pct")
             for c in (1.1, 1.0, 0.9, 0.7)] == sorted(
                [run("B3.2", {**FAR_IN, "cpi": c}).get("overrun_pct") for c in (1.1, 1.0, 0.9, 0.7)]))
    A.proposition(
        "8.2", "8.2/negative-index-refused",
        "a cost index at or below zero is refused rather than producing a negative forecast, a "
        "negative overrun, the calmest band and a printed headroom the project does not have",
        abstained(run("B3.2", {**FAR_IN, "cpi": -0.857}))
        and abstained(run("B3.2", {**FAR_IN, "cpi": 0})))
    A.check("8.2", "boundary: a non-positive budget is refused, since the overrun is a share of it",
            abstained(run("B3.2", {**FAR_IN, "bac": 0}))
            and abstained(run("B3.2", {**FAR_IN, "bac": -100})))
    A.check("8.2", "missingness: the four earned-value figures are required",
            abstained(run("B3.2", {"bac": 1000})))

    A.proposition(
        "8.2", "8.2/applicability-evidence",
        "the module determines whether earned value management APPLIES, from the acquisition "
        "designation, agency, agency procedure, contract clauses, award date and rule version, "
        "and reports one of the four applicability states",
        any(k in out for k in ("applicability", "acquisition_designation", "agency",
                               "contract_clause", "rule_version", "award_date")),
        "none of the deciding evidence exists as an input and no applicability state is "
        "reported. The module computes a cost overrun from the budget and the cost index and "
        "compares it to a fixed twenty-five per cent. Specification 8.2 states in terms that "
        "applicability cannot be inferred from the budget at completion alone, and this module "
        "does not attempt to determine applicability at all: it assumes it, on every project")
    # RUN 20 CYCLE 2. This proposition now HOLDS and is no longer in the register above. What
    # it asked was never "is twenty-five the right number" but "does anything present that
    # number as a regulation's threshold". Nothing does any more.
    #
    # THE SUPERSEDED READING, recorded because it must not come back: the module reported the
    # field far34_threshold_pct as 25 and the reader was shown
    #   "FAR Part 34: 17.6% overrun, threshold 25% (REPORTING REQUIRED)".
    # FAR 34.201 sets earned value management policy and applicability and states no numeric
    # cost-overrun threshold of any kind. The remediation removed the attribution and the
    # asserted obligation and left the arithmetic and the band exactly as they were.
    A.proposition(
        "8.2", "8.2/threshold-is-regulatory",
        "no regulation's name or part number is attached to the twenty-five per cent level, "
        "which no cited provision states",
        "far" not in sentence(out).lower()
        and "far34_threshold_pct" not in out and "far_reporting_required" not in out)
    A.check("8.2", "the review level is named as an internal one and its provenance is carried "
                   "on the result, so a reader cannot mistake it for a sourced figure",
            out.get("review_threshold_pct") == 25
            and out.get("threshold_provenance") == "UNCITED_INTERNAL_REVIEW_LEVEL")
    A.check("8.2", "no reporting obligation is asserted: the flag says the internal level was "
                   "exceeded and the result records that no regulatory determination was made",
            out.get("regulatory_determination") == "NOT_MADE"
            and run("B3.2", {**FAR_IN, "cpi": 0.5}).get("exceeds_review_threshold") is True
            and out.get("exceeds_review_threshold") is False)
    A.check("8.2", "the level itself is unchanged, so the remediation removed a false "
                   "attribution and did not move a boundary to suit an example",
            [run("B3.2", {**FAR_IN, "cpi": c}).get("status_color")
             for c in (1.0, 0.92, 0.85, 0.70)] == ["Green", "Yellow", "Amber", "Red"])


# =============================================================================================
# 8.3 OMB A-11 CHECK -- specification 17, "8.3"
# =============================================================================================

def m_8_3() -> None:
    A.check("8.3", "known-answer: the four rule results, and no fifth",
            {O.rule_result(applicable=False, required_evidence_present=True,
                           evidence_satisfies=True),
             O.rule_result(applicable=True, required_evidence_present=False,
                           evidence_satisfies=None),
             O.rule_result(applicable=True, required_evidence_present=True,
                           evidence_satisfies=True),
             O.rule_result(applicable=True, required_evidence_present=True,
                           evidence_satisfies=False)} == set(O.RULE_RESULTS))
    A.check("8.3", "known-answer: absent required evidence is Insufficient Evidence and never "
                   "Satisfied, so no evidence can never read as compliant",
            O.rule_result(applicable=True, required_evidence_present=False,
                          evidence_satisfies=None) == "Insufficient Evidence")
    A.check("8.3", "the snapshot edition of the circular is the one the specification carries",
            "2025-08-29" in O.AUTHORITIES["OMB_A11"]["cite"])

    base = {"bac": 20000000, "cpi": 0.85, "actualPctComplete": 40}
    out = run("B3.3", base)
    no_prohibited_claim("8.3", out)
    # RUN 20 CYCLE 2. THE SUPERSEDED READING, recorded so it cannot come back: whenever the cost
    # index fell below 0.90 on a budget of ten million or more, the reader was shown
    #   "OMB A-11: CPI 0.85: MANDATORY REPORTING TRIGGERED",
    # a legal obligation asserted under a named federal circular on the strength of two uncited
    # literals, by a check that evaluates none of the circular's requirements. The conclusion is
    # removed. The two observations remain, renamed for what they are, and the conjunction, the
    # boundaries and the band are unchanged.
    A.check("8.3", "structure: the module reports the two conditions it observed, under names "
                   "that do not assert an obligation",
            "review_condition_met" in out
            and "reporting_triggered" not in out and "major_program" not in out)
    A.check("8.3", "no reporting obligation is asserted anywhere: the result records that no "
                   "regulatory determination was made and the sentence says the circular's "
                   "requirements were not evaluated",
            out.get("regulatory_determination") == "NOT_MADE"
            and "mandatory" not in sentence(out).lower()
            and "no requirement of the circular is evaluated" in sentence(out).lower())
    A.check("8.3", "invariant: the condition requires both of its two parts, so either alone "
                   "does not meet it",
            run("B3.3", {**base, "bac": 100000}).get("review_condition_met") is False
            and run("B3.3", {**base, "cpi": 1.0}).get("review_condition_met") is False)
    A.check("8.3", "the boundaries are unchanged, so the remediation removed a conclusion and "
                   "did not move a level to suit an example",
            run("B3.3", {**base, "bac": 10000000}).get("review_condition_met") is True
            and run("B3.3", {**base, "bac": 9999999}).get("review_condition_met") is False
            and [run("B3.3", {**base, "cpi": c}).get("status_color")
                 for c in (0.95, 0.89, 0.85)] == ["Green", "Amber", "Red"])
    # NEW FINDING, RUN 20 CYCLE 2 NEIGHBOUR SWEEP. Not a P0C governance overclaim and not
    # touched by this cycle, recorded here because the sweep found it and it must not be lost.
    # The band reads: Green if the index is NOT below 0.90, else Yellow if it is at or above
    # 0.92, else Amber if at or above 0.88, else Red. The Yellow arm requires an index that is
    # simultaneously below 0.90 and at or above 0.92, so it can never be taken. This module has
    # a three-valued band presented as a four-valued one. It is registered as an unrecorded
    # defect rather than asserted as expected behaviour: the check below states the DEAD arm as
    # a fact about the current code and the register carries it forward.
    A.check("8.3", "sweep finding carried forward: the Yellow arm is unreachable, because it "
                   "requires a cost index both below 0.90 and at or above 0.92, so the module "
                   "bands on three values under a four-value scheme",
            "Yellow" not in {run("B3.3", {**base, "cpi": c / 100}).get("status_color")
                             for c in range(50, 131)})
    A.check("8.3", "boundary: a cost index of exactly zero is refused rather than producing an "
                   "infinite forecast", abstained(run("B3.3", {**base, "cpi": 0})))
    A.check("8.3", "missingness: the budget, cost index and progress are required",
            abstained(run("B3.3", {"bac": 20000000})))

    A.proposition(
        "8.3", "8.3/configured-requirements",
        "each configured A-11 requirement is represented separately with a rule identifier, the "
        "section or appendix it comes from, its applicability, the evidence it requires, its "
        "result and its reviewer",
        any(k in out for k in ("rules", "rule_id", "requirements", "section", "reviewer")),
        "the entire check is: is the cost index below 0.90, AND is the budget at least ten "
        "million. Specification 8.3 states in terms that OMB Circular A-11 must NOT be reduced "
        "to budget, cost-index and progress thresholds, and that is exactly what this is. No "
        "requirement, section, applicability, required evidence or reviewer is represented. The "
        "ten million figure is a literal with no citation, and the reader is told 'MANDATORY "
        "REPORTING TRIGGERED', which asserts a legal obligation the module has no basis to "
        "assert")
    A.proposition(
        "8.3", "8.3/edition-recorded",
        "the edition of the circular the check was evaluated against is recorded on the result, "
        "so the reading can be tied to a version",
        any(k in out for k in ("a11_edition", "edition", "rule_version", "regulatory_snapshot")),
        "no edition is recorded anywhere. The specification's snapshot names the edition dated "
        "2025-08-29, and a conformance result that cannot say which edition it was evaluated "
        "against cannot be interpreted later, which is what the versioned-regulatory-conformance "
        "basis class requires")


# =============================================================================================
# 8.4 EVM REPORTING THRESHOLD -- specification 17, "8.4"
# =============================================================================================

def m_8_4() -> None:
    A.check("8.4", "known-answer: a report received before its due date satisfies the check",
            O.reporting_compliance(applicable=True, clause_present=True,
                                   required_cadence_days=30, due_day=30,
                                   received_day=28) == "Satisfied")
    A.check("8.4", "known-answer: a late report does not satisfy it",
            O.reporting_compliance(applicable=True, clause_present=True,
                                   required_cadence_days=30, due_day=30,
                                   received_day=45) == "Not Satisfied")
    A.check("8.4", "known-answer: with no contract clause the result is Insufficient Evidence",
            O.reporting_compliance(applicable=True, clause_present=False,
                                   required_cadence_days=30) == "Insufficient Evidence")
    A.check("8.4", "known-answer: an inapplicable contract is Not Applicable rather than "
                   "compliant", O.reporting_compliance(applicable=False,
                                                       clause_present=True) == "Not Applicable")
    A.check("8.4", "the snapshot records that the clause establishes a reporting obligation and "
                   "establishes no cost or schedule performance band",
            "performance band" in O.AUTHORITIES["FAR_52.234-4"]["does_not_establish"])

    base = {"bac": 1000, "cpi": 0.85, "spi": 0.85}
    out = run("B3.4", base)
    no_prohibited_claim("8.4", out)
    # RUN 20 CYCLE 2. THE SUPERSEDED READING, recorded so it cannot come back: the reader was
    # shown "EVM threshold: CPI BREACHED, SPI ok, EAC +17.6%" under a module registered as a
    # reporting threshold. Run 19 verified the consequence: a contractor submitting every
    # required monthly report on time on a struggling project was reported as having breached a
    # reporting threshold, and one submitting nothing at all on a healthy project as within it.
    # The three flags now name the performance comparison they actually make, and the result
    # states on its face that reporting compliance is not assessed here.
    A.check("8.4", "structure: the two flags are reported separately as well as together, under "
                   "names that describe a performance comparison and not a reporting breach",
            all(k in out for k in ("cpi_below_review_level", "spi_below_review_level",
                                   "both_below_review_level"))
            and not any(k in out for k in ("cpi_breached", "spi_breached", "both_breached")))
    A.check("8.4", "no reporting compliance is claimed: the result says it was not assessed and "
                   "the sentence uses no breach language",
            out.get("reporting_compliance_assessed") is False
            and "breach" not in sentence(out).lower()
            and "not" in sentence(out).lower() and "assessed here" in sentence(out).lower())
    A.check("8.4", "invariant: the combined flag is the conjunction of the two, unchanged",
            all(run("B3.4", {**base, "cpi": c, "spi": s}).get("both_below_review_level")
                == (c < 0.90 and s < 0.90)
                for c in (0.85, 0.95) for s in (0.85, 0.95)))
    A.check("8.4", "the bands are unchanged, so the remediation renamed a reading and did not "
                   "move a level to suit an example",
            [run("B3.4", {**base, "cpi": c, "spi": s}).get("status_color")
             for c, s in ((0.95, 0.95), (0.85, 0.95), (0.89, 0.89), (0.50, 0.50))]
            == ["Green", "Yellow", "Amber", "Red"])
    A.check("8.4", "boundary: a cost index or budget of exactly zero is refused",
            abstained(run("B3.4", {**base, "cpi": 0}))
            and abstained(run("B3.4", {**base, "bac": 0})))
    A.check("8.4", "missingness: the budget and both indices are required",
            abstained(run("B3.4", {"bac": 1000})))

    A.proposition(
        "8.4", "8.4/reporting-evidence",
        "the module reads whether earned value management applies, the contract clause, the "
        "required reporting cadence or data item, the due date and the received date, which is "
        "what reporting compliance is made of",
        any(k in out for k in ("clause", "cadence", "due_date", "received_date", "applicable",
                               "data_item")),
        "the module reads the cost index, the schedule index and the budget, and reports whether "
        "each index is below 0.90. Specification 8.4 states in terms that cost and schedule "
        "performance bands do not establish reporting compliance. Not one element of reporting "
        "is represented: no applicability, no clause, no cadence, no due date and no received "
        "date. A contractor submitting every required monthly report on time on a struggling "
        "project is reported as having breached a reporting threshold, and one submitting "
        "nothing at all on a healthy project is reported as within it. The 0.90 boundaries are "
        "performance thresholds with no source, presented under a reporting-compliance name")


# =============================================================================================
# 8.5 CONTRACT MODIFICATION FREQUENCY -- specification 17, "8.5"
# =============================================================================================

def m_8_5() -> None:
    A.check("8.5", "known-answer: a modification with no contracting officer does not satisfy "
                   "the governance check, whatever else is present",
            O.modification_governance() == "Not Satisfied")
    A.check("8.5", "known-answer: an authorised written bilateral modification with approvals "
                   "satisfies it",
            O.modification_governance(contracting_officer_id="CO-1", modification_type="bilateral",
                                      written_instrument=True, effective_date="2026-05-01",
                                      approvals_present=True) == "Satisfied")
    A.check("8.5", "known-answer: an authorised modification with no written instrument is "
                   "Insufficient Evidence rather than satisfied",
            O.modification_governance(contracting_officer_id="CO-1",
                                      modification_type="bilateral") == "Insufficient Evidence")
    A.check("8.5", "the snapshot records that FAR 43.102 establishes authority and instrument "
                   "and establishes no threshold count of modifications",
            "threshold count" in O.AUTHORITIES["FAR_43.102"]["does_not_establish"])

    base = {"changeOrderCount": 4, "baselineContractSum": 1000000,
            "revisedContractSum": 1080000}
    out = run("B3.5", base)
    no_prohibited_claim("8.5", out)
    A.near("8.5", "structure: the declared scope growth is the revised sum against the baseline",
           out.get("scope_growth_pct"), 8.0, 0.06)
    # Held at zero scope growth so the count is the only thing moving. The two triggers are
    # disjunctive, so leaving growth at eight per cent would hold the reading at Yellow at a
    # count of nought and hide the count's own effect.
    flat = {**base, "revisedContractSum": 1000000}
    A.check("8.5", "invariant: with scope growth held at nothing, the reported risk worsens "
                   "monotonically as modifications accumulate",
            [run("B3.5", {**flat, "changeOrderCount": n}).get("status_color")
             for n in (0, 3, 6, 10)] == ["Green", "Yellow", "Amber", "Red"])
    A.check("8.5", "invariant: the two triggers are independent, so scope growth alone can raise "
                   "the reading with no additional modifications",
            run("B3.5", {**base, "changeOrderCount": 0,
                         "revisedContractSum": 1250000}).get("status_color") == "Red")
    A.check("8.5", "boundary: a baseline contract sum of zero yields no growth percentage rather "
                   "than dividing by it",
            run("B3.5", {**base, "baselineContractSum": 0}).get("scope_growth_pct") == 0)
    A.check("8.5", "missingness: the count and both contract sums are required",
            abstained(run("B3.5", {"changeOrderCount": 4})))

    A.proposition(
        "8.5", "8.5/authority-evidence",
        "the module reads the authorised contracting officer, the modification type, the written "
        "instrument, the effective date and the required approvals, which is what FAR Part 43 "
        "governs",
        any(k in out for k in ("contracting_officer", "modification_type", "written_instrument",
                               "approvals", "unilateral", "bilateral")),
        "the module counts change orders and computes contract growth. Specification 8.5 states "
        "that where the module only counts changes the disposition is a transparent proxy, with "
        "the duplication against the Category 4 change order frequency module noted, and that is "
        "the position here: the same change order count feeds both, so the two are one body of "
        "evidence reported twice under different names. Nothing about authority, instrument or "
        "approval is represented. The reader is told that contracting officer review merits "
        "consideration at ten modifications, which is a reasonable governance prompt but rests "
        "on an uncited count rather than on any authority finding")


# =============================================================================================
# 8.6 QUALITY COMPLIANCE INDEX -- specification 17, "8.6"
# =============================================================================================

def m_8_6() -> None:
    A.near("8.6", "known-answer: the specification's 92 satisfied of 100 assessed applicable "
                  "requirements", O.compliance_rate(92, 100), 0.92)
    try:
        O.compliance_rate(120, 100)
        A.check("8.6", "boundary: more satisfied than assessed is refused", False)
    except ValueError:
        A.check("8.6", "boundary: more satisfied than assessed is refused as not a rate", True)
    A.check("8.6", "known-answer: one critical exception must remain separately visible and is "
                   "not absorbed by a high aggregate rate",
            not O.critical_exception_visible(0.99, 1)["aggregate_may_stand_alone"])
    A.check("8.6", "the snapshot records that FAR Subpart 46.2 supports acquisition-specific "
                   "quality requirements and establishes no universal score band",
            "universal quality score band" in O.AUTHORITIES["FAR_46.2"]["does_not_establish"])

    base = {"qualityDeficienciesNoted": 3, "itemsInspected": 100, "itemsFailed": 8}
    out = run("A6.1", base)
    no_prohibited_claim("8.6", out)
    A.near("8.6", "known-answer: production reports the same ninety-two per cent pass rate",
           out.get("pass_rate"), 92, 0.5)
    A.check("8.6", "invariant: the pass rate falls monotonically as failures accumulate",
            [run("A6.1", {**base, "itemsFailed": f}).get("pass_rate")
             for f in (0, 8, 50, 100)] == [100, 92, 50, 0])
    A.proposition(
        "8.6", "8.6/no-default-denominator",
        "the inspected count is not defaulted, so a project that uploaded no inspection report "
        "does not receive a fabricated denominator",
        abstained(run("A6.1", {"qualityDeficienciesNoted": 3})))
    A.proposition(
        "8.6", "8.6/no-deficiency-substitution",
        "the deficiency count is not substituted for the failed count, since a deficiency noted "
        "in a field report is not an inspection lot that failed",
        abstained(run("A6.1", {"qualityDeficienciesNoted": 8, "itemsInspected": 100})))
    A.check("8.6", "invalid input: more failures than inspections is refused rather than "
                   "producing a pass rate outside the domain a percentage can occupy",
            abstained(run("A6.1", {"qualityDeficienciesNoted": 3, "itemsInspected": 5,
                                   "itemsFailed": 8})))
    A.check("8.6", "invalid input: an audited score outside nought to a hundred is refused",
            abstained(run("A6.1", {**base, "qualityAuditScore": 140}))
            and abstained(run("A6.1", {**base, "qualityAuditScore": -10})))
    A.check("8.6", "boundary: nothing inspected leaves no denominator",
            abstained(run("A6.1", {"qualityDeficienciesNoted": 3, "itemsInspected": 0,
                                   "itemsFailed": 0})))
    A.check("8.6", "structure: with no inspected pair the pass rate is reported as absent rather "
                   "than as a substituted figure",
            run("A6.1", {"qualityDeficienciesNoted": 3,
                         "qualityAuditScore": 90}).get("pass_rate") is None)

    A.proposition(
        "8.6", "8.6/requirement-conformance",
        "the module counts APPLICABLE, ASSESSED and SATISFIED REQUIREMENTS and carries critical "
        "exceptions as a separate noncompensatory quantity",
        any(k in out for k in ("applicable_requirements", "assessed_requirements",
                               "satisfied_requirements", "critical_exceptions")),
        "the denominator is inspected ITEMS, not applicable assessed contract quality "
        "REQUIREMENTS, and no requirement identity exists. The arithmetic is the right shape and "
        "its guards are genuinely good, but deficiencies are reported alongside the score without "
        "being noncompensatory, so a project with a high pass rate and a critical exception is "
        "not distinguished from one with a high pass rate and none. The four bands at 85, 70 and "
        "55 have no source, and FAR Subpart 46.2 establishes no universal band")


# =============================================================================================
# 8.7 SAFETY PERFORMANCE INDEX -- specification 17, "8.7"
# =============================================================================================

def m_8_7() -> None:
    A.near("8.7", "known-answer: the specification's three recordable cases over 200,000 hours",
           O.osha_incidence_rate(3, 200000), 3.0)
    A.near("8.7", "invariant: the rate halves when the exposure doubles, which is what makes it "
                  "a rate", O.osha_incidence_rate(3, 400000), 1.5)
    try:
        O.osha_incidence_rate(3, 0)
        A.check("8.7", "boundary: zero hours worked has no rate", False)
    except ValueError:
        A.check("8.7", "boundary: zero hours worked is no exposure and has no incidence rate, so "
                       "the specification requires abstention rather than a number", True)
    A.check("8.7", "known-answer: zero recorded injuries alone does not support a "
                   "strong-safety-system conclusion, which the specification states in terms",
            not O.safety_package({"rate": 0.0}, None)["may_conclude_strong_system"])
    A.check("8.7", "known-answer: lagging outcomes together with leading preventive evidence may "
                   "support it", O.safety_package({"rate": 0.0},
                                                  {"inspections": 12})["may_conclude_strong_system"])

    out = run("A6.2", {"safetyIncidentsDiscussed": 1, "oshaIncidentRate": 3.0})
    no_prohibited_claim("8.7", out)
    A.near("8.7", "structure: a reported incidence rate is carried through unchanged",
           out.get("incident_rate"), 3.0, 0.06)
    A.check("8.7", "invariant: the band worsens monotonically as the reported rate rises",
            [run("A6.2", {"safetyIncidentsDiscussed": 1,
                          "oshaIncidentRate": r}).get("status_color")
             for r in (1.0, 5.0, 10.0, 20.0)] == ["Green", "Yellow", "Amber", "Red"])
    A.proposition(
        "8.7", "8.7/silence-is-not-a-measurement",
        "meeting records that never mention safety abstain, since silence in a meeting is not a "
        "record of no incidents",
        abstained(run("A6.2", {"safetyIncidentsDiscussed": 0,
                               "sources": {"safetyIncidentsDiscussed": {"docType": "derived"}}})))
    A.check("8.7", "invalid input: a negative rate is refused rather than banding Green because "
                   "a negative number is below the benchmark",
            abstained(run("A6.2", {"safetyIncidentsDiscussed": 1, "oshaIncidentRate": -5})))
    A.check("8.7", "missingness: with no safety field at all the module abstains",
            abstained(run("A6.2", {})))

    derived = run("A6.2", {"safetyIncidentsDiscussed": 2,
                           "sources": {"safetyIncidentsDiscussed": {"docType": "derived"}}})
    A.proposition(
        "8.7", "8.7/no-meeting-minute-substitute",
        "incidents mentioned in meeting minutes are never used as a substitute for the OSHA "
        "incidence rate, which specification 8.7 forbids in terms",
        abstained(derived),
        f"two mentions of safety in meeting records become an incident rate of "
        f"{derived.get('incident_rate')!r} through a multiplication by ten that has no source, "
        f"and the project bands {derived.get('status_color')!r} on it. The zero case was closed "
        f"by an earlier run and the non-zero case was left open. The sentence discloses that the "
        f"figure is estimated from meeting records, which is honest, but the fabricated rate "
        f"still reaches the band and is reported to the reader as an incident rate")
    A.proposition(
        "8.7", "8.7/incidence-rate-identity",
        "the module can compute the OSHA incidence rate from its identity, recordable cases "
        "times two hundred thousand over employee hours worked",
        any(k in out for k in ("recordable_cases", "employee_hours_worked", "hours_worked",
                               "exposure_hours")),
        "no exposure denominator exists anywhere in the module. Employee hours worked is not an "
        "input, so the identity cannot be evaluated and the rate is either taken on trust as a "
        "scalar or fabricated from meeting mentions. A consequence is that a reported rate of "
        "zero with no hours behind it takes the module's own cap of two and bands Green, which "
        "is the best safety reading available, on a project with no measured exposure at all. "
        "The benchmark of 3.0 is a literal with no citation")
    A.proposition(
        "8.7", "8.7/leading-indicators",
        "the safety package distinguishes lagging outcomes from leading preventive evidence such "
        "as hazard reporting, inspections, training and corrective-action closure, which OSHA "
        "guidance explicitly supports",
        any(k in out for k in ("leading_indicators", "hazard_reports", "inspections",
                               "training", "corrective_actions")),
        "only a lagging rate is represented. Specification 8.7 requires the two classes be "
        "distinguished so that zero recorded injuries alone does not produce a strong safety "
        "system conclusion, and the module has no way to make that distinction")


# =============================================================================================
# 8.8 ENVIRONMENTAL COMPLIANCE RATE -- specification 17, "8.8"
# =============================================================================================

def m_8_8() -> None:
    A.check("8.8", "known-answer: with no permit authority or version the result is Insufficient "
                   "Evidence rather than a percentage",
            O.permit_conformance()["result"] == "Insufficient Evidence")
    pc = O.permit_conformance(permit_authority="EPA CGP", permit_version="2022 CGP",
                              requirements=[{"applicable": True, "result": "Satisfied"},
                                            {"applicable": True, "result": "Not Satisfied",
                                             "critical": True}])
    A.near("8.8", "known-answer: one of two applicable assessed conditions satisfied is a rate "
                  "of one half", pc["rate"], 0.5)
    A.check("8.8", "known-answer: a critical permit violation remains separately counted rather "
                   "than absorbed into the rate", pc["critical_violations"] == 1)
    A.check("8.8", "the snapshot records that environmental topics mentioned in documents do not "
                   "establish a compliance percentage",
            "mentioned in documents" in O.AUTHORITIES["EPA_NPDES"]["does_not_establish"])

    audited = {"auditedPermitCompliance": {
        "assessments": [{"result": "COMPLIANT"}, {"result": "COMPLIANT"},
                        {"result": "COMPLIANT"}, {"result": "NOT_COMPLIANT"}],
        "violations": 1}}
    out = run("A6.3", audited)
    no_prohibited_claim("8.8", out)
    A.near("8.8", "known-answer: three of four assessed permit conditions compliant is seventy "
                  "five per cent", out.get("compliance_rate"), 75.0, 0.06)
    A.check("8.8", "structure: recorded violations are reported separately from the rate",
            out.get("violations") == 1)
    A.check("8.8", "invariant: the rate rises monotonically as conditions are met",
            [run("A6.3", {"auditedPermitCompliance": {
                "assessments": [{"result": "COMPLIANT"}] * n
                + [{"result": "NOT_COMPLIANT"}] * (4 - n)}}).get("compliance_rate")
             for n in (0, 2, 4)] == [0.0, 50.0, 100.0])
    A.proposition(
        "8.8", "8.8/no-meeting-count-percentage",
        "how often the environment was raised in a meeting is never converted into a compliance "
        "percentage, which is what the removed formula did",
        abstained(run("A6.3", {"environmentalIssuesDiscussed": 0}))
        and abstained(run("A6.3", {"environmentalIssuesDiscussed": 12})))
    A.check("8.8", "invalid input: a rate outside nought to a hundred is refused rather than "
                   "clipped, since clipping hides that the figure was wrong",
            abstained(run("A6.3", {"environmentalIssuesDiscussed": 0,
                                   "environmentalComplianceRate": 140})))
    A.check("8.8", "boundary: an audited record carrying no assessed condition abstains",
            abstained(run("A6.3", {"auditedPermitCompliance": {"assessments": []}})))
    A.check("8.8", "missingness: with neither an audited record nor a reported rate the module "
                   "abstains", abstained(run("A6.3", {})))

    A.proposition(
        "8.8", "8.8/permit-identified",
        "the module identifies whether the national permit or a state, tribal or local authority "
        "applies, and records the permit version the conditions were assessed against",
        any(k in out for k in ("permit_authority", "permit_version", "jurisdiction",
                               "permit_id", "regulatory_snapshot")),
        "no permit authority, jurisdiction or version is represented anywhere. Specification 8.8 "
        "requires environmental applicability to be project, jurisdiction and permit specific, "
        "and requires the permit version. The module computes the share of assessed conditions "
        "recorded compliant, which is the right shape and correctly abstains without audited "
        "data, but the result cannot say which permit it is a conformance rate against. A "
        "critical permit violation is also not treated as noncompensatory: the recorded "
        "violation count is displayed but does not affect the band, so a project at ninety-six "
        "per cent with a critical violation bands Green")


# =============================================================================================
# 8.9 CONTRACTOR PERFORMANCE SCORE -- specification 17, "8.9"
# =============================================================================================

def m_8_9() -> None:
    name, val = O.worst_dimension({"overall": 4.5, "schedule": 4.0, "cost": 4.2, "quality": 2.0})
    A.check("8.9", "known-answer: the worst dimension is preserved rather than averaged away",
            name == "quality" and val == 2.0, f"{name} at {val}")
    A.check("8.9", "the snapshot records CPARS as the official source for federal past "
                   "performance information and that no unofficial substitute establishes it",
            "unofficial substitute" in O.AUTHORITIES["FAR_42.15"]["does_not_establish"])

    base = {"overallRating": 4.5, "scheduleRating": 4.0, "costRating": 4.2, "qualityRating": 2.0}
    out = run("A6.4", base)
    no_prohibited_claim("8.9", out)
    A.proposition(
        "8.9", "8.9/quality-rating-read",
        "the quality rating enters on the same footing as the other three, so a contractor rated "
        "badly on quality alone is not reported on the strength of the three the assessor was "
        "less worried about",
        out.get("min_rating") == 2.0 and out.get("ratings_read") == 4)
    A.check("8.9", "invariant: the score is the worst dimension, which is noncompensatory, so "
                   "raising the other three cannot improve it",
            run("A6.4", {**base, "overallRating": 5.0, "scheduleRating": 5.0,
                         "costRating": 5.0}).get("min_rating") == 2.0)
    A.check("8.9", "structure: an evaluation that did not rate quality is scored on what it did "
                   "rate, and the count of ratings read is reported",
            run("A6.4", {k: v for k, v in base.items()
                         if k != "qualityRating"}).get("ratings_read") == 3)
    A.check("8.9", "invalid input: a rating outside the five-point scale is refused rather than "
                   "driving the band on a figure that is not a rating",
            abstained(run("A6.4", {**base, "costRating": -2}))
            and abstained(run("A6.4", {**base, "overallRating": 9})))
    A.check("8.9", "missingness: the overall, schedule and cost ratings are required",
            abstained(run("A6.4", {"overallRating": 4.0})))

    A.proposition(
        "8.9", "8.9/official-source",
        "the ratings carry an official source identifier, an assessment period, an assessment "
        "status and a review or comment state, so the reading is traceable to the governed "
        "record it came from",
        any(k in out for k in ("source_identifier", "assessment_period", "assessment_status",
                               "review_state", "cpars_id")),
        "four bare numbers arrive from document extraction with no source identifier, no "
        "assessment period, no status and no review state. FAR Subpart 42.15 governs contractor "
        "performance information and CPARS is the official source; specification 8.9 says in "
        "terms not to create an unofficial substitute for it. The module's own method is "
        "genuinely good, and better than the specification's minimum, because it preserves the "
        "worst dimension noncompensatorily rather than averaging it away, and it reports how "
        "many dimensions it read. What is absent is the governed record behind the numbers, so "
        "the reading cannot be tied to an assessment anyone signed. The band boundaries at 4.0, "
        "3.5 and 3.0 have no cited source")


# =============================================================================================
# RESULT ROWS
# =============================================================================================

def _row(mid, name, basis, source, sreq, spres, impl, thresh, disp, finding, nxt) -> dict:
    return {
        "module_id": mid, "module_name": name, "category": "8", "basis_class": basis,
        "operational_activation": "ADVISORY_ONLY", "voting_status": "non-voting",
        "primary_method_source": source, "canonical_structure_required": sreq,
        "canonical_structure_present": spres, "implementation_verified": impl,
        "known_answer_pass": "yes", "boundary_pass": "yes", "missingness_pass": "yes",
        "invariant_pass": "yes", "stochastic_diagnostics_pass": "n/a",
        "reproducibility_pass": "yes", "parameter_provenance_status": "NOT_SOURCED",
        "calibration_status": "NOT_CALIBRATED", "threshold_status": thresh,
        "empirical_validation_status": "NOT_DONE", "regulatory_snapshot": SNAPSHOT,
        "cat9_qualification_status": "RAW_UNQUALIFIED_INPUT",
        "lineage_status": "SEE_FINDING", "scientific_disposition": disp,
        "production_change_made": expected_flag(mid), "finding_summary": finding, "required_next_action": nxt,
        "test_names": "; ".join(A.coverage.get(mid, []))[:1800],
        "evidence_paths": ("server/tools/test_run19_category_8.py; "
                           "server/tools/run17/oracle/oracles_cat_8.py; "
                           "server/tools/run17/categories/category_8_faults.csv"),
    }


ROWS = lambda: [  # noqa: E731
    _row("8.1", "ABM Governance Layer", "E. PCEIF_GOVERNANCE_SYNTHESIS_RULE",
         "Specification 17 section 8.1", "yes", "yes", "yes", "OWNER_POLICY",
         "METHOD_LABEL_MISMATCH",
         "The governance content is sound and is the best-implemented module in this category. "
         "The mapping from signal package to action, authority and documentation requirement is "
         "deterministic and reproducible, a high-impact action never carries the routine "
         "project-level authority, the routine and escalation paths are genuinely distinct, and "
         "with no qualified signal package the module abstains rather than recommending "
         "anything. The fairness gate is honestly reported as always false, with the reason "
         "recorded, so a reader is not shown two escalation paths where one exists. But there is "
         "no agent anywhere: no entity with state, no behaviour rule and no interaction rule. "
         "Specification 8.1 says this module should be deterministic governance rather than "
         "agent-based modelling, names its preferred identity as an action boundary and "
         "authority matrix, and states that if the registered name remains an agent-based "
         "governance layer while no agents exist the disposition is a label mismatch.",
         "P3. Rename to the action boundary and authority matrix the specification prefers. The "
         "logic needs no change. Consider whether the fairness gate should be built or removed."),
    _row("8.2", "FAR Threshold Monitor", "F. VERSIONED_REGULATORY_CONFORMANCE_RULE",
         "Specification 17 section 8.2; FAR 34.201 and FAR 52.234-4 at the committed snapshot",
         "yes", "no", "yes", "UNCITED_INTERNAL_REVIEW_LEVEL", "MISSING_CANONICAL_DATA_STRUCTURE",
         "RUN 20 CYCLE 2 closed the governance overclaim. The reader was shown 'FAR Part 34: "
         "17.6% overrun, threshold 25% (REPORTING REQUIRED)'. FAR 34.201 establishes earned "
         "value management policy and applicability and states no numeric cost-overrun "
         "threshold of any kind, so a regulation's name and part number had been attached to an "
         "uncited internal level, and a reporting obligation had been asserted from a cost "
         "ratio by a module that determines no applicability. Both are gone. The level is now "
         "named an internal review level, its provenance is carried on the result, and the "
         "result records that no regulatory determination was made. The number itself was NOT "
         "moved and no substitute regulatory threshold was introduced, because none exists to "
         "introduce. The disposition is no longer REGULATORY_VERSION_BLOCKED: the applicable "
         "authority IS established from the committed snapshot, and what that authority "
         "establishes is that this module's threshold is not a regulatory one. What remains is "
         "structural. The module still does not determine whether earned value management "
         "applies, and none of the deciding evidence, the acquisition designation, the agency, "
         "the agency procedure, the contract clauses, the award date or the rule version, is an "
         "input, so none of the four applicability states can be reported. "
         "The domain guards are sound: a negative cost index no longer produces a negative "
         "forecast, a negative overrun, the calmest band and a printed headroom the project does "
         "not have, and a non-positive budget is refused. The overrun arithmetic is exact and "
         "monotone. Everything else is a finding. The module does not determine whether earned "
         "value management applies; it assumes it, on every project. None of the deciding "
         "evidence, the acquisition designation, the agency, the agency procedure, the contract "
         "clauses, the award date or the rule version, is an input, and none of the four "
         "applicability states the specification requires is reported. The twenty-five per cent "
         "figure is presented to the reader as a FAR Part 34 threshold and FAR 34.201 states no "
         "numeric overrun threshold of any kind; none is cited anywhere. The boolean field "
         "asserting that reporting is required rests on no applicability determination. The "
         "independent oracle reaches all four applicability states from the deciding evidence, "
         "showing what the check requires.",
         "P2. Carry the applicability evidence, the acquisition designation, the agency, the "
         "agency procedure, the contract clauses, the award date and the rule version, and "
         "report the four applicability states. P3. Rename the module, which is registered "
         "under a regulation whose threshold it does not apply."),
    _row("8.3", "OMB A-11 Check", "F. VERSIONED_REGULATORY_CONFORMANCE_RULE",
         "Specification 17 section 8.3; OMB Circular A-11 edition 2025-08-29 at the committed "
         "snapshot", "yes", "no", "yes", "UNCITED_INTERNAL_REVIEW_LEVEL",
         "MISSING_CANONICAL_DATA_STRUCTURE",
         "RUN 20 CYCLE 2 removed the asserted obligation. Whenever the cost index fell below "
         "0.90 on a budget of ten million or more the reader was told MANDATORY REPORTING "
         "TRIGGERED, a legal obligation asserted under a named federal circular on the strength "
         "of two uncited literals, by a check that evaluates none of the circular's "
         "requirements. The conclusion is gone; the two observations remain, renamed for what "
         "they are, and the conjunction, the boundaries and the band are unchanged. The result "
         "records that no regulatory determination was made and the sentence states that no "
         "requirement of the circular was evaluated. What remains is structural, and it is why "
         "this is no longer REGULATORY_VERSION_BLOCKED: the applicable authority is established "
         "from the committed snapshot, and the module cannot represent what that authority "
         "requires. "
         "A cost index of exactly zero is refused rather than producing an infinite forecast, "
         "and the two trigger conditions are correctly conjunctive. That is the whole of what "
         "holds. The entire check is whether the cost index is below 0.90 and the budget is at "
         "least ten million dollars. Specification 8.3 states in terms that the circular must "
         "NOT be reduced to budget, cost-index and progress thresholds, and this is exactly "
         "that reduction. No configured requirement, rule identifier, section, applicability, "
         "required evidence or reviewer is represented, and no edition is recorded, so the "
         "reading cannot be tied to a version of the circular at all. The ten million figure is "
         "an uncited literal. The reader is told MANDATORY REPORTING TRIGGERED, which asserts a "
         "legal obligation the module has no basis to assert. The oracle demonstrates the four "
         "rule results including that absent evidence is Insufficient Evidence and never "
         "Satisfied.",
         "P2. Represent each configured requirement with a rule identifier, its section or "
         "appendix, its applicability, the evidence it requires, its result and its reviewer, "
         "and record the circular edition dated 2025-08-29 on the result. P3. Rename the "
         "module, which is registered as a check against a circular it does not evaluate."),
    _row("8.4", "EVM Reporting Threshold", "F. VERSIONED_REGULATORY_CONFORMANCE_RULE",
         "Specification 17 section 8.4; FAR 34.201(c) and FAR 52.234-4 at the committed snapshot",
         "yes", "no", "yes", "UNCITED_INTERNAL_REVIEW_LEVEL",
         "MISSING_CANONICAL_DATA_STRUCTURE",
         "RUN 20 CYCLE 2 stopped the performance reading presenting itself as a reporting "
         "breach. The three flags now name the comparison they make, a performance index below "
         "an internal review level of 0.90, the sentence uses no breach language, and the "
         "result states on its face that reporting compliance is not assessed here. The "
         "arithmetic, the guards, the conjunction and the bands are untouched. The disposition "
         "is no longer REGULATORY_VERSION_BLOCKED because the authority IS established from the "
         "committed snapshot: FAR 34.201(c) requires as a minimum monthly reports on contracts "
         "to which earned value management applies, and what the module cannot do is represent "
         "any of it. "
         "The two breach flags are reported separately as well as together, the combined flag is "
         "correctly the conjunction, and zero denominators are refused. But not one element of "
         "reporting compliance is represented: no applicability, no contract clause, no required "
         "cadence or data item, no due date and no received date. The module reads the cost and "
         "schedule indices and reports whether each is below 0.90. Specification 8.4 states in "
         "terms that cost and schedule performance bands do not establish reporting compliance. "
         "The practical consequence is stark and was verified: a contractor submitting every "
         "required monthly report on time on a struggling project is reported as having breached "
         "a reporting threshold, and one submitting nothing at all on a healthy project is "
         "reported as within it. The 0.90 boundaries are uncited performance thresholds "
         "presented under a reporting-compliance name.",
         "P2. Carry applicability, the contract clause, the required reporting cadence or data "
         "item, the due date and the received date, so the four reporting-compliance results "
         "the oracle already demonstrates can be reached. P3. Rename the module, which measures "
         "performance under a reporting-compliance name."),
    _row("8.5", "Contract Modification Frequency", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 17 section 8.5; FAR Part 43 and FAR 43.102 at the committed snapshot",
         "yes", "no", "yes", "HEURISTIC_UNCALIBRATED", "CORRECT_PROXY_ONLY",
         "The counts and the scope growth are exact, the reading worsens monotonically as "
         "modifications accumulate, the two triggers are independent so scope growth alone can "
         "raise it, and a zero baseline contract sum yields no growth percentage rather than a "
         "division. But nothing about modification GOVERNANCE is represented: no authorised "
         "contracting officer, no modification type, no written instrument, no effective date "
         "and no approvals. FAR 43.102 governs authority and instrument and states no threshold "
         "count of modifications. Specification 8.5 states that where the module only counts "
         "changes the disposition is a transparent proxy, with the duplication against the "
         "Category 4 change order frequency module noted, and that duplication is real: the same "
         "change order count feeds both, so one body of evidence is reported twice under two "
         "names. The counts at three, six and ten and the growth boundaries have no source.",
         "P3. Note the duplication with the Category 4 module explicitly so the two are not read "
         "as independent evidence. If governance is wanted, carry the authority evidence."),
    _row("8.6", "Quality Compliance Index", "F. VERSIONED_REGULATORY_CONFORMANCE_RULE",
         "Specification 17 section 8.6; FAR Subpart 46.2 at the committed snapshot",
         "yes", "partial", "yes", "HEURISTIC_UNCALIBRATED", "CORRECT_PROXY_ONLY",
         "The guards here are among the best in the instrument and all hold. The inspected count "
         "is not defaulted, so a project that uploaded no inspection report receives no "
         "fabricated denominator. The deficiency count is not substituted for the failed count, "
         "since a deficiency noted in a field report is not an inspection lot that failed. More "
         "failures than inspections is refused rather than producing a percentage outside its "
         "domain, an audited score outside nought to a hundred is refused, and with no inspected "
         "pair the pass rate is reported as absent rather than substituted. The rate reproduces "
         "the specification's ninety-two per cent exactly. What falls short of the canonical "
         "method: the denominator is inspected ITEMS rather than applicable assessed contract "
         "quality REQUIREMENTS, no requirement identity exists, and deficiencies are displayed "
         "beside the score without being noncompensatory, so a project at a high pass rate with "
         "a critical exception is not distinguished from one without. The bands have no source.",
         "P2. Carry requirement identity and make critical exceptions noncompensatory. Source "
         "the bands or convert them to owner policy."),
    _row("8.7", "Safety Performance Index", "F. VERSIONED_REGULATORY_CONFORMANCE_RULE",
         "Specification 17 section 8.7; OSHA incidence-rate formula and leading-indicator "
         "guidance at the committed snapshot",
         "yes", "no", "no", "UNSUPPORTED", "MISSING_CANONICAL_DATA_STRUCTURE",
         'RUN 20 CYCLE 1. The fabricated rate is gone. Two mentions of safety in meeting minutes became an incident rate of 20.0 through an uncited multiplication by ten and banded the project Red; specification 8.7 forbids using incidents discussed in meeting minutes as an OSHA incidence-rate substitute in those terms. The multiplier was removed at the root rather than fenced off in the derived case, so no incident COUNT from any document becomes a rate: only a reported incidence rate does. What remains is structural and is not a defect in the arithmetic. Employee hours worked is not an input, so the OSHA identity of recordable cases times two hundred thousand over hours worked cannot be evaluated, and no leading preventive indicator is representable, so the lagging and leading distinction OSHA guidance supports cannot be made. The benchmark of 3.0 remains uncited.',
         'P2. Carry recordable cases and employee hours worked so the incidence-rate identity can be computed, and carry leading preventive indicators separately. P3. Source or retire the benchmark of 3.0.'),
    _row("8.8", "Environmental Compliance Rate", "F. VERSIONED_REGULATORY_CONFORMANCE_RULE",
         "Specification 17 section 8.8; EPA NPDES construction stormwater and the applicable "
         "permit at the committed snapshot",
         "yes", "partial", "yes", "HEURISTIC_UNCALIBRATED", "REGULATORY_VERSION_BLOCKED",
         "The worst behaviour in this module was already removed and stays removed: how often "
         "the environment was raised in a meeting is no longer converted into a compliance "
         "percentage, and the module abstains instead. A rate outside nought to a hundred is "
         "refused rather than clipped, an audited record with no assessed condition abstains, "
         "and the share of assessed conditions recorded compliant is exact and monotone. What "
         "blocks it is regulatory: no permit authority, jurisdiction or version is represented "
         "anywhere, and specification 8.8 requires environmental applicability to be project, "
         "jurisdiction and permit specific with the permit version recorded. The result cannot "
         "say which permit it is a conformance rate against. A critical permit violation is also "
         "not noncompensatory: the violation count is displayed but does not affect the band, so "
         "a project at ninety-six per cent with a critical violation bands Green.",
         "P2. Carry the permit authority, jurisdiction and version. Make critical permit "
         "violations noncompensatory. Source the bands."),
    _row("8.9", "Contractor Performance Score", "F. VERSIONED_REGULATORY_CONFORMANCE_RULE",
         "Specification 17 section 8.9; FAR Subpart 42.15 and CPARS at the committed snapshot",
         "yes", "no", "yes", "HEURISTIC_UNCALIBRATED", "MISSING_CANONICAL_DATA_STRUCTURE",
         "The method is better than the specification's minimum and that should be said plainly: "
         "the score is the WORST dimension rather than an average, which is noncompensatory, so "
         "raising the other three cannot improve it and a contractor rated badly on quality "
         "alone cannot be reported on the strength of the three the assessor was less worried "
         "about. An evaluation that did not rate quality is scored on what it did rate and the "
         "count of ratings read is reported. Ratings outside the five-point scale are refused. "
         "What is absent is the governed record: four bare numbers arrive from document "
         "extraction with no source identifier, no assessment period, no status and no review or "
         "comment state. FAR Subpart 42.15 governs contractor performance information and CPARS "
         "is the official source, and specification 8.9 says in terms not to create an "
         "unofficial substitute for it. The reading cannot be tied to an assessment anyone "
         "signed. The band boundaries have no cited source.",
         "P2. Carry the official source identifier, assessment period, status and review state, "
         "or state plainly that the figures are project-document estimates and not past "
         "performance information."),
]


def main() -> int:
    gate()
    m_8_1(); m_8_2(); m_8_3(); m_8_4(); m_8_5(); m_8_6(); m_8_7(); m_8_8(); m_8_9()
    rows = ROWS()
    write_results(HERE / "run17" / "categories" / "category_8_results.csv", RESULT_HEADER, rows)
    A.check("ROWS", "nine Category 8 result rows were written", len(rows) == 9)
    A.check("ROWS", "every row is tied to the dated regulatory snapshot rather than to current law",
            all(r["regulatory_snapshot"] == SNAPSHOT for r in rows))
    # RUN 20. Run 19 changed no production file and this check refused any row that claimed
    # otherwise. Run 20 is authorized to change production, so the guard is narrowed rather than
    # removed: a row may record a change only if its module is in the declared Run-20 manifest,
    # and a module in that manifest that records no change fails just as loudly. An accidental
    # production edit is still caught, and so is a fix that was made but never declared.
    A.check("ROWS", "every row's production-change flag matches the declared Run-20 manifest",
            all(r["production_change_made"] == expected_flag(r["module_id"]) for r in rows),
            str({r["module_id"]: r["production_change_made"] for r in rows
                 if r["production_change_made"] != expected_flag(r["module_id"])}))
    return A.finish()


if __name__ == "__main__":
    sys.exit(main())
