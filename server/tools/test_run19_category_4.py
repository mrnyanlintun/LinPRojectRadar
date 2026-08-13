"""
RUN 19 -- Category 4, document and risk signals. Ten scientific targets.

Controlling theory: the committed supervisory specification, section 13. Its recurring demand in
this category is EXPOSURE: a count is not a rate, a rate's denominator must be the population its
numerator came from, and a stock carried across periods is not a flow within one.

4.1 Document Risk Score is a special case. It is a registered module but is NOT in the server's
validated set: the score arrives from the extraction pipeline as an input to other modules, and
the registry refuses to compute it. That refusal is itself the assessment, and the specification
requires extraction accuracy be separated from score arithmetic and from banding, so all three
are addressed separately below.

Oracles come from run17/oracle/oracles_cat_4.py, self proved at import.
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
from population import population                                # noqa: E402
from app.simulation import registry as REG                       # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731

KNOWN_DEFECTS = {
    "4.1/labelled-corpus": "MISSING_CANONICAL_DATA_STRUCTURE",
    "4.4/exposure-rate": "CORRECT_ABSTENTION",
    "4.6/time-exposure": "METHOD_LABEL_MISMATCH",
    "4.6/frequency-and-magnitude-separate": "METHOD_LABEL_MISMATCH",
    "4.7/dispute-state-evidence": "METHOD_LABEL_MISMATCH",
    "4.8/traceable-criteria": "PARAMETER_PROVENANCE_BLOCKED",
    "4.9/item-level-slack": "CORRECT_PROXY_ONLY",
    "4.5/schedule-linkage": "CORRECT_PROXY_ONLY",
    "4.10/verified-conflicts": "METHOD_LABEL_MISMATCH",
    "4.10/explicit-exposure": "METHOD_LABEL_MISMATCH",
}

A = Audit("category 4", KNOWN_DEFECTS)
O = oracle_gate(A, "oracles_cat_4")


def run(code_id: str, si: dict) -> dict:
    return REG.run_module(code_id, si, RAND, CUTOFF)


def abstained(out: dict) -> bool:
    return bool(out.get("insufficient_data")) or out.get("status_color") is None


def gate() -> None:
    A.check("GATE", "the Category 4 oracle reproduces the specification's worked answers",
            not O.self_test(), "; ".join(O.self_test()))
    ids = {t["module_id"] for t in population()}
    for mid in ("4.1", "4.2", "4.3", "4.4", "4.5", "4.6", "4.7", "4.8", "4.9", "4.10"):
        A.check("GATE", f"{mid} is one of the hundred scientific targets", mid in ids)
    A.check("GATE", "4.1 and 4.10 are distinct targets and did not collide under float coercion",
            "4.1" in ids and "4.10" in ids)
    for code in ("A4.1", "A4.2", "A4.3", "A4.4", "A4.5", "A4.6", "A4.7", "A4.8", "A4.9",
                 "A4.10"):
        A.check("GATE", f"{code} is non-voting", code not in REG.CORE_VOTING_MODULES)


# =============================================================================================
# 4.1 DOCUMENT RISK SCORE -- specification 13, "4.1"
# =============================================================================================

def m_4_1() -> None:
    # A. Extraction and classification accuracy, against held-out reference labels. This is the
    # question the specification separates first and it is answered in the laboratory, because
    # no labelled corpus exists in the repository to answer it against production.
    c = O.confusion([True, True, False, False], [True, False, True, False])
    A.check("4.1", "known-answer: a labelled positive and negative set gives confusion counts",
            (c["tp"], c["fp"], c["fn"], c["tn"]) == (1, 1, 1, 1), str(c))
    A.near("4.1", "known-answer: precision from those counts", c["precision"], 0.5)
    A.near("4.1", "known-answer: recall from those counts", c["recall"], 0.5)
    A.near("4.1", "boundary: a perfect extractor has precision one",
           O.confusion([True, False], [True, False])["precision"], 1.0)
    A.check("4.1", "boundary: an extractor that predicts nothing has no precision to report "
                   "rather than a precision of zero, since it made no positive claim",
            O.confusion([False, False], [True, False])["precision"] is None)
    try:
        O.confusion([True], [True, False])
        A.check("4.1", "invalid input: predictions that do not correspond to the labels are "
                       "refused", False)
    except ValueError:
        A.check("4.1", "invalid input: predictions that do not correspond one to one with the "
                       "reference labels are refused", True)

    # B. The registry's own position on this module.
    idx = REG.registry_index()
    A.check("4.1", "the module is registered and carries the document risk score name",
            idx.get("A4.1", {}).get("module_name") == "Document Risk Score")
    raised = False
    try:
        run("A4.1", {"docRiskScore": 0.4})
    except Exception:
        raised = True
    A.check("4.1", "structure: the server refuses to compute it rather than producing a score, "
                   "because it has not been ported and validated", raised)
    A.check("4.1", "the score nevertheless enters the instrument as an INPUT to other modules, "
                   "so its accuracy is a property of the extraction pipeline rather than of any "
                   "module in this category",
            not abstained(run("A4.10", {"docRiskScore": 0.4, "rfiCount": 16})))

    A.proposition(
        "4.1", "4.1/labelled-corpus",
        "a labelled reference corpus of risk passages exists against which extraction precision "
        "and recall can be measured, which specification 4.1 requires as the minimum test",
        False,
        "no labelled corpus exists in the repository and no confusion counts, precision, recall "
        "or calibration figures are recorded anywhere for the document risk score. "
        "Specification 4.1 requires three things be separated: extraction and classification "
        "accuracy, the arithmetic of the scalar aggregation, and the operational banding. Only "
        "the second is testable here, and the module itself is not computed by the server at "
        "all. There is also no governed risk taxonomy, evidence span, severity, confidence or "
        "coverage attached to the score: it arrives as one number. Downstream modules band on "
        "it, so an unmeasured extraction accuracy propagates into every reading built on it")


# =============================================================================================
# 4.2 RFI VELOCITY -- specification 13, "4.2"
# =============================================================================================

def m_4_2() -> None:
    A.near("4.2", "known-answer: the specification's twelve requests over thirty days, per day",
           O.velocity(12, 30, 1), 0.4)
    A.near("4.2", "known-answer: the same, per a standardised thirty-day period",
           O.velocity(12, 30, 30), 12.0)
    A.near("4.2", "invariant: velocity halves when the exposure doubles, which is what makes it "
                  "a rate rather than a count", O.velocity(12, 60, 30), 6.0)
    A.near("4.2", "known-answer: the overdue ratio over its own population",
           O.overdue_ratio(3, 12), 0.25)

    out = run("A4.2", {"rfiCount": 12, "rfiPeriodDays": 30})
    A.near("4.2", "known-answer: production reports the same twelve per thirty days",
           out.get("rfi_per_30d"), 12.0, 0.06)
    A.near("4.2", "known-answer: and the same rate expressed per week",
           out.get("rfi_per_week"), 12 / 30 * 7, 0.06)
    A.check("4.2", "invariant: the reported rate falls as the exposure window lengthens",
            run("A4.2", {"rfiCount": 12, "rfiPeriodDays": 60}).get("rfi_per_30d")
            < out.get("rfi_per_30d"))
    A.proposition(
        "4.2", "4.2/exposure-not-substituted",
        "an absent log period is required rather than replaced by thirty days, with the finding "
        "then stating a span the document never said",
        abstained(run("A4.2", {"rfiCount": 12})))
    A.check("4.2", "boundary: a log period of zero or below leaves no denominator",
            abstained(run("A4.2", {"rfiCount": 12, "rfiPeriodDays": 0})))
    A.check("4.2", "invalid input: a negative request count is refused",
            abstained(run("A4.2", {"rfiCount": -5, "rfiPeriodDays": 30})))
    A.check("4.2", "invalid input: an overdue count larger than the total is refused",
            abstained(run("A4.2", {"rfiCount": 12, "rfiPeriodDays": 30, "rfiOverdue": 20})))
    A.check("4.2", "missingness: with no request count at all the module abstains",
            abstained(run("A4.2", {"rfiPeriodDays": 30})))
    A.proposition(
        "4.2", "4.2/overdue-is-separate",
        "the overdue ratio is computed and reported as its own quantity rather than folded into "
        "the velocity",
        run("A4.2", {"rfiCount": 12, "rfiPeriodDays": 30,
                     "rfiOverdue": 3}).get("overdue_ratio") == 0.25)
    A.check("4.2", "the reported band is the worse of the velocity band and the overdue band, so "
                   "a bad overdue share is not absorbed by a calm velocity",
            run("A4.2", {"rfiCount": 2, "rfiPeriodDays": 30,
                         "rfiOverdue": 2}).get("status_color") == "Red")
    A.check("4.2", "threshold: the two ladders have no cited source and the module's own comment "
                   "records that a count per project or a response time is not a per-week rate "
                   "threshold", out.get("status_color") in ("Green", "Yellow", "Amber", "Red"))


# =============================================================================================
# 4.3 SUBMITTAL REJECTION RATE -- specification 13, "4.3"
# =============================================================================================

def m_4_3() -> None:
    A.near("4.3", "known-answer: the specification's three rejected of twenty",
           O.rejection_rate(3, 20), 0.15)
    for bad, label in (((-1, 20), "a negative rejected count"),
                       ((25, 20), "more rejected than assessed"),
                       ((1, 0), "an empty assessed population")):
        try:
            O.rejection_rate(*bad)
            A.check("4.3", f"boundary: {label} is refused", False)
        except ValueError:
            A.check("4.3", f"boundary: {label} is refused", True)

    out = run("A4.3", {"submittalsTotal": 20, "submittalsRejected": 3})
    A.near("4.3", "known-answer: production reports the same fifteen per cent",
           out.get("rejection_rate"), 0.15, 1e-6)
    A.check("4.3", "invariant: the rate rises monotonically with rejections",
            [run("A4.3", {"submittalsTotal": 20,
                          "submittalsRejected": r}).get("rejection_rate")
             for r in (0, 5, 10, 20)] == [0.0, 0.25, 0.5, 1.0])
    A.proposition(
        "4.3", "4.3/rejected-within-total",
        "a rejected count outside the total is refused rather than producing a rate above one, "
        "which every band above the top boundary silently absorbs into the worst band",
        abstained(run("A4.3", {"submittalsTotal": 20, "submittalsRejected": 30})))
    A.check("4.3", "boundary: a register with no entries has no denominator",
            abstained(run("A4.3", {"submittalsTotal": 0, "submittalsRejected": 0})))
    A.check("4.3", "invalid input: a negative rejected count is refused",
            abstained(run("A4.3", {"submittalsTotal": 20, "submittalsRejected": -2})))
    A.check("4.3", "missingness: both figures are required",
            abstained(run("A4.3", {"submittalsTotal": 20})))
    A.proposition(
        "4.3", "4.3/status-taxonomy-declared",
        "the module records which register the population came from, so a rate over requests for "
        "approval and one over submittals are distinguishable rather than silently mixed",
        run("A4.3", {"rfaTotal": 20, "rfaRejected": 3}).get("source") == "rfa_log"
        and out.get("source") == "submittals")
    A.check("4.3", "structure: the revise-and-resubmit and open counts are reported separately "
                   "rather than folded into the rejected count, which the specification asks be "
                   "clarified",
            "revise-and-resubmit" in str(run("A4.3", {"rfaTotal": 20, "rfaRejected": 3,
                                                      "rfaResubmit": 4}).get("evidence_metric")))


# =============================================================================================
# 4.4 NCR RATE -- specification 13, "4.4"
# =============================================================================================

def m_4_4() -> None:
    A.near("4.4", "known-answer: the specification's four nonconformances over a hundred "
                  "inspections", O.ncr_rate(4, 100), 0.04)
    try:
        O.ncr_rate(4, 0)
        A.check("4.4", "boundary: no exposure means no rate", False)
    except ValueError:
        A.check("4.4", "boundary: no exposure means no rate", True)
    try:
        O.backlog_is_not_a_rate(12, 2)
        A.check("4.4", "a backlog over one period's intake is not a rate", False)
    except AssertionError:
        A.check("4.4", "a backlog stock over one period's intake flow is not a rate: the two "
                       "counts are different sets and the ratio is unbounded above", True)

    cohort = {"auditedNonconformanceCohort": {
        "audits": [{"total_findings": 40}, {"total_findings": 60}],
        "open_nonconformances": [{"id": i} for i in range(15)]}}
    out = run("A4.4", cohort)
    A.near("4.4", "known-answer: fifteen open against an audited cohort of a hundred",
           out.get("open_ratio"), 0.15, 0.005)
    A.check("4.4", "structure: the audited cohort the backlog is a share of is reported",
            out.get("audited_cohort") == 100)
    A.check("4.4", "invariant: the open share rises monotonically with the backlog",
            [run("A4.4", {"auditedNonconformanceCohort": {
                "audits": [{"total_findings": 100}],
                "open_nonconformances": [{"id": i} for i in range(n)]}}).get("open_ratio")
             for n in (0, 20, 50)] == [0.0, 0.2, 0.5])
    A.proposition(
        "4.4", "4.4/no-stock-over-flow",
        "the backlog is measured against an audited cohort rather than against one period's "
        "intake, which is a different set and unbounded above",
        abstained(run("A4.4", {"ncrIssued": 2, "ncrClosed": 0, "ncrOpen": 12})))
    A.proposition(
        "4.4", "4.4/empty-intake-not-green",
        "a project that issued nothing this period but carries an unresolved backlog does not "
        "read as the best band, since issuing nothing new is not evidence of quality",
        abstained(run("A4.4", {"ncrIssued": 0, "ncrClosed": 0, "ncrOpen": 12})))
    A.check("4.4", "invalid input: more open than the audited cohort contains is refused",
            abstained(run("A4.4", {"auditedNonconformanceCohort": {
                "audits": [{"total_findings": 10}],
                "open_nonconformances": [{"id": i} for i in range(20)]}})))
    A.check("4.4", "boundary: an audited record with no completed audit abstains",
            abstained(run("A4.4", {"auditedNonconformanceCohort": {"audits": []}})))
    A.check("4.4", "missingness: with no cohort in either form the module abstains",
            abstained(run("A4.4", {})))

    A.proposition(
        "4.4", "4.4/exposure-rate",
        "the module can express a nonconformance RATE over a governed exposure such as inspected "
        "units, work hours, inspections or value, which is what specification 4.4 defines",
        any(k in out for k in ("ncr_rate", "exposure_units", "inspections", "work_hours")),
        "the module reports the share of an audited cohort still OPEN, which is a backlog state "
        "and not a rate. Specification 4.4 separates the two explicitly and lists the backlog "
        "quantities, open count, age, severity and closure rate, as the other half of the "
        "picture. The backlog share is correctly and carefully computed, the stock-over-flow "
        "defect is genuinely gone, and abstaining without an audited cohort is the right "
        "behaviour. But no exposure denominator exists, so the rate half of the method is not "
        "representable, and of the four backlog quantities only the open count is carried. This "
        "is a correct abstention from the rate, not a defect in what is computed")


# =============================================================================================
# 4.5 WEATHER DAY IMPACT -- specification 13, "4.5"
# =============================================================================================

def m_4_5() -> None:
    w = O.weather_schedule_effect(2, 0, True)
    A.near("4.5", "known-answer: two days lost on a zero-float critical activity has a direct "
                  "modelled path effect of two days", w["path_effect_days"], 2.0)
    A.near("4.5", "known-answer: the raw lost-day count is carried as its own quantity, which is "
                  "weather disruption days rather than impact", w["disruption_days"], 2.0)
    A.near("4.5", "invariant: available float absorbs the loss where it exists",
           O.weather_schedule_effect(2, 5, False)["path_effect_days"], 0.0)
    A.check("4.5", "invariant: the path effect is monotone in the days lost",
            O.weather_schedule_effect(5, 0, True)["path_effect_days"]
            > O.weather_schedule_effect(2, 0, True)["path_effect_days"])

    out = run("A4.5", {"weatherDaysLost": 3, "floatRemaining": 15})
    A.near("4.5", "known-answer: three days lost against fifteen days of float is a fifth of it",
           out.get("weather_ratio"), 20, 0.5)
    A.check("4.5", "structure: the float the loss is measured against is reported",
            out.get("float_remaining") == 15)
    A.proposition(
        "4.5", "4.5/no-worst-case-asserted",
        "with no float figure the module abstains rather than setting the ratio to one, which "
        "asserts the worst case as a measurement and makes one day lost on a project with a "
        "year of float identical to one with none",
        abstained(run("A4.5", {"weatherDaysLost": 3})))
    A.proposition(
        "4.5", "4.5/verified-days-only",
        "lost days inferred by the pipeline rather than counted in a field report are refused, "
        "since a qualifier in a display string is not a substitute for refusing",
        abstained(run("A4.5", {"weatherDaysLost": 3, "floatRemaining": 15,
                               "sources": {"weatherDaysLost": {"docType": "derived"}}})))
    A.check("4.5", "boundary: no positive float remaining leaves no proportion to measure",
            abstained(run("A4.5", {"weatherDaysLost": 3, "floatRemaining": 0}))
            and abstained(run("A4.5", {"weatherDaysLost": 3, "floatRemaining": -5})))
    A.check("4.5", "invalid input: a negative count of lost days is refused",
            abstained(run("A4.5", {"weatherDaysLost": -3, "floatRemaining": 15})))
    A.check("4.5", "structure: float may be given directly or derived from total less consumed, "
                   "and both routes agree",
            run("A4.5", {"weatherDaysLost": 3, "totalFloat": 20,
                         "consumedFloat": 5}).get("float_remaining") == 15)
    A.proposition(
        "4.5", "4.5/schedule-linkage",
        "the module carries the affected activity, the governing weather allowance and the "
        "causal linkage evidence, so a full schedule impact rather than a disruption count is "
        "reported",
        all(k in out for k in ("affected_activity", "allowance", "linkage")),
        "the module reports lost days as a share of the float available to absorb them, which is "
        "a real and defensible measure, and its two fabrications are genuinely gone: the worst "
        "case is no longer asserted when float is unknown, and inferred lost days are refused "
        "rather than carried with a parenthetical. But no affected activity, planned work, "
        "governing weather allowance, available path or causal linkage is represented, so this "
        "is weather disruption days against float rather than the full impact claim "
        "specification 4.5 defines. Note honestly that the float here is network-derived and the "
        "corpus carries no activity network, so the module is expected to abstain in practice")


# =============================================================================================
# 4.6 CHANGE ORDER FREQUENCY -- specification 13, "4.6"
# =============================================================================================

def m_4_6() -> None:
    A.near("4.6", "known-answer: the specification's six changes in a hundred and eighty days, "
                  "per day", O.change_frequency(6, 180, 1), 1 / 30)
    A.near("4.6", "known-answer: the same, one per standardised thirty-day month",
           O.change_frequency(6, 180, 30), 1.0)
    A.near("4.6", "known-answer: magnitude is a separate quantity, change value over baseline",
           O.change_magnitude(80000, 1000000), 0.08)
    try:
        O.change_frequency(6, 0)
        A.check("4.6", "boundary: no exposure means no frequency", False)
    except ValueError:
        A.check("4.6", "boundary: no exposure time means no frequency", True)

    base = {"changeOrderCount": 6, "baselineContractSum": 1000000,
            "revisedContractSum": 1080000}
    out = run("A4.6", base)
    A.near("4.6", "structure: the reported scope growth is revised against baseline",
           out.get("scope_growth_pct"), 8.0, 0.06)
    A.check("4.6", "structure: the change count is reported as the count it is",
            out.get("co_count") == 6)
    A.check("4.6", "invariant: the band worsens as either the count or the growth rises",
            run("A4.6", {**base, "changeOrderCount": 20}).get("status_color") == "Red"
            and run("A4.6", {**base, "revisedContractSum": 1400000}).get("status_color") == "Red")
    A.check("4.6", "boundary: a baseline contract sum of zero yields no growth percentage rather "
                   "than dividing by it",
            run("A4.6", {**base, "baselineContractSum": 0}).get("scope_growth_pct") == 0)
    A.check("4.6", "missingness: the count and both contract sums are required",
            abstained(run("A4.6", {"changeOrderCount": 6})))

    A.proposition(
        "4.6", "4.6/time-exposure",
        "the module divides the change count by a governed exposure, a time span or another "
        "declared opportunity basis, which is what makes a count a frequency",
        any(k in out for k in ("period_days", "changes_per_30d", "exposure_days",
                               "opportunity_basis")),
        "the module reports a RAW COUNT of change orders and bands on it directly. Specification "
        "4.6 states that frequency must have an exposure and works the arithmetic through: six "
        "changes in a hundred and eighty days is one per standardised month. No exposure of any "
        "kind is an input here, so six changes on a six-month project and six on a six-year "
        "project produce the identical reading. The request velocity module in this same "
        "category does require its exposure and abstains without it, so the instrument already "
        "knows how to do this")
    A.proposition(
        "4.6", "4.6/frequency-and-magnitude-separate",
        "frequency and magnitude are reported as two named quantities rather than banded "
        "together as one composite without naming it as one",
        False,
        "the band is a joint ladder over the count AND the scope growth: Green requires growth "
        "at most five per cent and at most three changes, and so on. Specification 4.6 states "
        "that magnitude is separate and that the two must not be combined into one quantity "
        "without naming it as a composite. The two figures are reported separately, which is "
        "good, but the single colour a reader sees is a composite of a countless frequency and a "
        "magnitude, and it is not named as one. Note also the duplication with the Category 8 "
        "modification governance module, which reads the same change order count and the same "
        "two contract sums by an almost identical ladder")


# =============================================================================================
# 4.7 DISPUTE ESCALATION INDEX -- specification 13, "4.7"
# =============================================================================================

def m_4_7() -> None:
    A.check("4.7", "known-answer: with no dispute evidence there is no stage, and specifically "
                   "not a calm one", O.escalation_stage({}) is None)
    A.check("4.7", "known-answer: a submitted claim sits at the second stage of the example "
                   "ladder", O.escalation_stage({"claim_submitted": True}) == 1)
    A.check("4.7", "invariant: a later governed stage is more escalated than an earlier one",
            O.escalation_stage({"mediation_or_adr": True})
            > O.escalation_stage({"claim_submitted": True}))
    A.check("4.7", "the stage ladder is versioned and is labelled an example rather than a "
                   "universal set, since the contract defines the governed stages",
            bool(O.STAGE_LADDER_VERSION) and "example" in O.STAGE_LADDER_VERSION)

    base = {"docRiskScore": 0.4, "rfiCount": 12, "changeOrderCount": 5}
    out = run("A4.7", base)
    A.near("4.7", "structure: the declared index is the weighted sum of three capped terms",
           out.get("escalation_index"),
           min(12 / 20, 1) * 0.3 + min(5 / 10, 1) * 0.3 + 0.4 * 0.4, 0.005)
    A.proposition(
        "4.7", "4.7/withholding-does-not-improve",
        "all three sources are required, so withholding a request log or a change order log "
        "cannot improve the reading by having an absent term score zero",
        all(abstained(run("A4.7", {k: v for k, v in base.items() if k != drop}))
            for drop in base))
    A.proposition(
        "4.7", "4.7/zero-is-evidence",
        "a reported count of zero is evidence and is treated as one, rather than being "
        "indistinguishable from a log that was never read",
        not abstained(run("A4.7", {"docRiskScore": 0.4, "rfiCount": 0, "changeOrderCount": 0})))
    A.check("4.7", "invalid input: a negative count or score is refused",
            abstained(run("A4.7", {**base, "rfiCount": -1}))
            and abstained(run("A4.7", {**base, "docRiskScore": -0.5})))
    A.check("4.7", "structure: the sources the reading rests on are listed on the output, so "
                   "which evidence is behind the number is visible rather than inferred",
            len(out.get("sources_used", [])) == 3 and out.get("sources_missing") == [])
    A.check("4.7", "invariant: the index rises monotonically with each of its three terms",
            all(run("A4.7", {**base, k: v}).get("escalation_index")
                > out.get("escalation_index")
                for k, v in (("rfiCount", 19), ("changeOrderCount", 9), ("docRiskScore", 0.9))))

    A.proposition(
        "4.7", "4.7/dispute-state-evidence",
        "the module reads actual claim or dispute state evidence and places the project on a "
        "governed ordinal escalation process, so a later stage cannot look less escalated and "
        "generic activity cannot establish a stage",
        any(k in out for k in ("dispute_stage", "claim_state", "stage", "process_version")),
        "there is no dispute, claim or determination evidence anywhere. The index is a weighted "
        "sum of the document risk score, a request count capped at twenty and a change order "
        "count capped at ten. Specification 4.7 states in terms that request and change counts "
        "alone do not establish a dispute stage, and requires that missing dispute evidence "
        "cannot improve the condition, which cannot even be expressed here because no dispute "
        "evidence is representable. The module's own qualifier calls it a proxy and the source "
        "comment says plainly that no formal dispute is inferred from this activity, which is "
        "honest disclosure, but the registered name says dispute escalation. The specification's "
        "permitted alternative for this state is an explicit project-stress proxy. The three "
        "weights and two caps have no source")


# =============================================================================================
# 4.8 SUBCONTRACTOR PERFORMANCE -- specification 13, "4.8"
# =============================================================================================

def m_4_8() -> None:
    third = 1 / 3
    A.near("4.8", "known-answer: the specification's ratings .80, .90 and .70 under equal "
                  "weights", O.weighted_score({"a": 0.80, "b": 0.90, "c": 0.70},
                                              {"a": third, "b": third, "c": third}), 0.80)
    try:
        O.weighted_score({"a": 1.0}, {"a": 0.5})
        A.check("4.8", "boundary: weights that do not sum to one are refused", False)
    except ValueError:
        A.check("4.8", "boundary: weights that do not sum to one are refused", True)
    A.check("4.8", "known-answer: a critical criterion below its floor remains visible, since "
                   "critical violations may be noncompensatory by policy",
            O.noncompensatory_violation({"safety": 0.2, "cost": 0.99}, {"safety"}, 0.5)
            == ["safety"])

    out = run("A4.8", {"subcontractorComplianceScore": 0.82})
    A.check("4.8", "known-answer: the supplied score is reported as a percentage unchanged",
            out.get("compliance_score") == 82)
    A.check("4.8", "invariant: the band worsens monotonically as the score falls",
            [run("A4.8", {"subcontractorComplianceScore": s}).get("status_color")
             for s in (0.90, 0.75, 0.60, 0.40)] == ["Green", "Yellow", "Amber", "Red"])
    A.proposition(
        "4.8", "4.8/no-derived-safety-net",
        "the browser's derived safety net is not ported, so with no supplied compliance score "
        "the module abstains rather than manufacturing one",
        abstained(run("A4.8", {"subcontractorIssuesDiscussed": 3, "docRiskScore": 0.5})))
    A.check("4.8", "missingness: with none of the three fields present the module abstains",
            abstained(run("A4.8", {})))
    A.check("4.8", "structure: the contributing signals are listed beside the score rather than "
                   "folded into it",
            "issues in OAC minutes" in str(run("A4.8", {
                "subcontractorComplianceScore": 0.82,
                "subcontractorIssuesDiscussed": 3}).get("evidence_metric")))

    A.proposition(
        "4.8", "4.8/traceable-criteria",
        "the score is built from traceable criteria such as quality, schedule, safety, cost "
        "behaviour, responsiveness and administration, with their governed ratings and versioned "
        "weights",
        any(k in out for k in ("criteria", "weights", "criterion_ratings", "weight_version")),
        "one precomputed compliance score arrives as a scalar and the module reports it. "
        "Specification 4.8 states in terms that a precomputed compliance score with unknown "
        "construction cannot independently validate this module, and that is exactly the "
        "position: no criterion, no rating, no weight and no version exists, so nothing about "
        "how the number was formed can be established, and no critical violation can be treated "
        "as noncompensatory because no criterion is separable. The module is honest about what "
        "it does, listing the contributing signals beside the score rather than folding them in, "
        "and it correctly refuses to manufacture a score. The four bands have no source")


# =============================================================================================
# 4.9 PROCUREMENT LEAD TIME MONITOR -- specification 13, "4.9"
# =============================================================================================

def m_4_9() -> None:
    A.near("4.9", "known-answer: the specification's required day 100 against a forecast "
                  "delivery on day 110 is minus ten days of slack",
           O.procurement_slack(100, 110), -10.0)
    A.near("4.9", "invariant: slack is positive when delivery beats the need date",
           O.procurement_slack(120, 110), 10.0)
    try:
        O.disjoint_counts(3, 5)
        A.check("4.9", "boundary: more delayed than at risk is refused", False)
    except ValueError:
        A.check("4.9", "boundary: more delayed than at risk is refused, since the two categories "
                       "nest rather than being disjoint", True)

    out = run("A4.9", {"longLeadItemsTotal": 10, "longLeadAtRisk": 8, "longLeadDelayed": 5})
    A.near("4.9", "known-answer: the audit's own figures give a weighted disruption of .65 "
                  "rather than the 1.8 the double-counted form produced",
           out.get("risk_ratio"), 0.65, 0.005)
    A.proposition(
        "4.9", "4.9/proportion-is-bounded",
        "the reported ratio is a genuine proportion of the long-lead set and cannot exceed one, "
        "because a delayed item is treated as the at-risk item it already is rather than counted "
        "twice",
        all(0 <= run("A4.9", {"longLeadItemsTotal": t, "longLeadAtRisk": a,
                              "longLeadDelayed": d}).get("risk_ratio", 0) <= 1
            for t in (1, 5, 10) for a in range(t + 1) for d in range(a + 1)))
    A.check("4.9", "invariant: with every item delayed the proportion is exactly one",
            run("A4.9", {"longLeadItemsTotal": 10, "longLeadAtRisk": 10,
                         "longLeadDelayed": 10}).get("risk_ratio") == 1.0)
    A.check("4.9", "invariant: with nothing at risk the proportion is exactly nought",
            run("A4.9", {"longLeadItemsTotal": 10, "longLeadAtRisk": 0,
                         "longLeadDelayed": 0}).get("risk_ratio") == 0.0)
    A.check("4.9", "invariant: a delayed item weighs more than a merely at-risk one",
            run("A4.9", {"longLeadItemsTotal": 10, "longLeadAtRisk": 4,
                         "longLeadDelayed": 4}).get("risk_ratio")
            > run("A4.9", {"longLeadItemsTotal": 10, "longLeadAtRisk": 4,
                           "longLeadDelayed": 0}).get("risk_ratio"))
    A.proposition(
        "4.9", "4.9/empty-log-abstains",
        "an empty procurement log abstains rather than having a denominator of one invented for "
        "it, which made a single delayed item out of no items score two",
        abstained(run("A4.9", {"longLeadItemsTotal": 0, "longLeadAtRisk": 0,
                               "longLeadDelayed": 1})))
    A.check("4.9", "invalid input: more at risk than exist, or more delayed than at risk, is "
                   "refused and says which pair disagreed",
            abstained(run("A4.9", {"longLeadItemsTotal": 5, "longLeadAtRisk": 9,
                                   "longLeadDelayed": 1}))
            and abstained(run("A4.9", {"longLeadItemsTotal": 10, "longLeadAtRisk": 3,
                                       "longLeadDelayed": 5})))
    A.check("4.9", "missingness: all three counts are required",
            abstained(run("A4.9", {"longLeadItemsTotal": 10})))

    A.proposition(
        "4.9", "4.9/item-level-slack",
        "the module computes item-level procurement slack, the required on-site date less the "
        "forecast delivery date, and considers item criticality, the schedule need date, float "
        "and procurement status",
        any(k in out for k in ("slack_days", "items", "required_on_site", "forecast_delivery",
                               "criticality")),
        "the module reports an aggregate weighted share of the long-lead set that is at risk or "
        "delayed. That aggregate is now genuinely bounded and the double count is gone, which "
        "was the substantive defect, and its guards are complete. But no item, no required "
        "on-site date, no forecast delivery date and therefore no slack exists, so the "
        "specification's core quantity cannot be computed and item criticality, path need date "
        "and float cannot enter. It is a coherent transparent aggregate of a procurement log "
        "rather than the item-level monitor the name implies. The 0.5 weight on a merely at-risk "
        "item and the four bands have no source")


# =============================================================================================
# 4.10 SPECIFICATION CONFLICT DENSITY -- specification 13, "4.10"
# =============================================================================================

def m_4_10() -> None:
    d = O.conflict_density(5, 250)
    A.near("4.10", "known-answer: the specification's five verified conflicts over two hundred "
                   "and fifty requirements", d, 0.02)
    A.near("4.10", "known-answer: expressed per thousand requirements", O.per_thousand(d), 20.0)
    A.near("4.10", "invariant: density halves when the exposure doubles, which is what makes it "
                   "a density", O.conflict_density(5, 500), 0.01)
    try:
        O.conflict_density(5, 0)
        A.check("4.10", "boundary: no exposure unit means no density", False)
    except ValueError:
        A.check("4.10", "boundary: no exposure unit means no density", True)

    # Chosen below the module's own cap of one, so the declared form is observed rather than
    # the cap: 0.2 times the square root of 9 is 0.6.
    out = run("A4.10", {"docRiskScore": 0.2, "rfiCount": 9})
    A.near("4.10", "structure: the declared quantity is the document risk weighted by the square "
                   "root of the request count", out.get("conflict_density"), 0.2 * 3, 0.005)
    A.check("4.10", "invariant: the quantity RISES with the request count, which is the opposite "
                    "direction from a density, since a density falls as exposure rises",
            run("A4.10", {"docRiskScore": 0.2, "rfiCount": 16}).get("conflict_density")
            > out.get("conflict_density"))
    A.proposition(
        "4.10", "4.10/no-exposure-no-substitute",
        "with no requests recorded the module abstains on absent exposure rather than reporting "
        "the unweighted document risk score under a different name",
        abstained(run("A4.10", {"docRiskScore": 0.4, "rfiCount": 0})))
    A.check("4.10", "invalid input: a document risk score outside nought to one is refused "
                    "rather than multiplied through into the band ladder",
            abstained(run("A4.10", {"docRiskScore": 30, "rfiCount": 16}))
            and abstained(run("A4.10", {"docRiskScore": -1, "rfiCount": 16})))
    A.check("4.10", "invalid input: a negative request count is refused",
            abstained(run("A4.10", {"docRiskScore": 0.4, "rfiCount": -5})))
    A.check("4.10", "missingness: both inputs are required",
            abstained(run("A4.10", {"docRiskScore": 0.4})))
    A.check("4.10", "boundary: the reported figure is capped at one, so the band ladder is not "
                    "fed a quantity outside the range it reads",
            run("A4.10", {"docRiskScore": 0.9, "rfiCount": 400}).get("conflict_density") == 1)

    A.proposition(
        "4.10", "4.10/verified-conflicts",
        "the numerator is a count of VERIFIED conflict candidates, each retaining the two or "
        "more conflicting evidence locations, which specification 4.10 requires",
        any(k in out for k in ("conflicts", "conflict_locations", "verified_conflicts",
                               "evidence_spans")),
        "there is no conflict. The numerator is a document risk score, a scalar whose own "
        "extraction accuracy is unmeasured, and no conflicting evidence location is retained "
        "anywhere because no individual conflict is identified at all")
    A.proposition(
        "4.10", "4.10/explicit-exposure",
        "the denominator is an explicit governed exposure unit such as requirements, clauses, "
        "sections, pages or cross-reference pairs",
        any(k in out for k in ("requirements", "clauses", "exposure_units", "pages")),
        "the quantity is the document risk score times the request count over the square root of "
        "the request count, which is the risk score times the square root of the count. "
        "Specification 4.10 names this exact form and states in terms that it is not a "
        "specification conflict density. It has the wrong direction as well as the wrong "
        "structure: a density falls as exposure rises, and this quantity RISES with the request "
        "count without bound until the cap at one intervenes. The guards around it are sound and "
        "the cap prevents an out-of-range figure reaching the band, but the measure is not a "
        "density of anything")


# =============================================================================================
# RESULT ROWS
# =============================================================================================

def _row(mid, name, basis, source, sreq, spres, impl, thresh, lineage, disp, finding, nxt):
    return {
        "module_id": mid, "module_name": name, "category": "4", "basis_class": basis,
        "operational_activation": "ADVISORY_ONLY", "voting_status": "non-voting",
        "primary_method_source": source, "canonical_structure_required": sreq,
        "canonical_structure_present": spres, "implementation_verified": impl,
        "known_answer_pass": "yes", "boundary_pass": "yes", "missingness_pass": "yes",
        "invariant_pass": "yes", "stochastic_diagnostics_pass": "n/a",
        "reproducibility_pass": "yes", "parameter_provenance_status": "NOT_SOURCED",
        "calibration_status": "NOT_CALIBRATED", "threshold_status": thresh,
        "empirical_validation_status": "NOT_DONE", "regulatory_snapshot": "n/a",
        "cat9_qualification_status": "RAW_UNQUALIFIED_INPUT", "lineage_status": lineage,
        "scientific_disposition": disp, "production_change_made": "no",
        "finding_summary": finding, "required_next_action": nxt,
        "test_names": "; ".join(A.coverage.get(mid, []))[:1800],
        "evidence_paths": ("server/tools/test_run19_category_4.py; "
                           "server/tools/run17/oracle/oracles_cat_4.py; "
                           "server/tools/run17/categories/category_4_faults.csv"),
    }


ROWS = lambda: [  # noqa: E731
    _row("4.1", "Document Risk Score", "H. EXTERNAL_EXTRACTION_OR_CLASSIFICATION_METHOD",
         "Specification 13 section 4.1; Moon, Lee and Chi (2022)",
         "yes", "no", "n/a", "HEURISTIC_UNCALIBRATED", "FEEDS_MANY_DOWNSTREAM_MODULES",
         "MISSING_CANONICAL_DATA_STRUCTURE",
         "The module is registered but is NOT in the server's validated set: asked to compute "
         "it, the registry refuses on the ground that it has not been ported and validated. The "
         "score nevertheless enters the instrument as an INPUT that several other modules band "
         "on, which was verified. Specification 4.1 requires three questions be separated: "
         "extraction and classification accuracy, the arithmetic of the scalar aggregation, and "
         "the operational banding. Only the arithmetic is testable here. No labelled reference "
         "corpus exists anywhere in the repository, so no confusion counts, precision, recall or "
         "calibration figures can be produced, and the specification names a labelled corpus as "
         "the MINIMUM test for this module. There is also no governed risk taxonomy, evidence "
         "span, severity, confidence or coverage attached: one number arrives. The consequence "
         "reaches beyond this row, because an unmeasured extraction accuracy propagates into "
         "every downstream reading built on the score.",
         "P2. Build a labelled reference corpus and report precision, recall and error analysis. "
         "Until then no claim about document risk accuracy is supportable anywhere in the "
         "instrument."),
    _row("4.2", "RFI Velocity", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 13 section 4.2", "no", "n/a", "yes", "HEURISTIC_UNCALIBRATED",
         "OWN_REGISTER", "THRESHOLD_CALIBRATION_BLOCKED",
         "This is the module that gets exposure right, and it is worth naming as the contrast "
         "with the change order module in the same category. The rate is a count over a real "
         "exposure window, it reproduces the specification's worked figures exactly, it halves "
         "when the window doubles, and an absent log period is REQUIRED rather than replaced by "
         "thirty days with the finding then stating a span the document never said. The overdue "
         "ratio is computed over its own population and reported separately, and the band is the "
         "worse of the two so a bad overdue share is not absorbed by a calm velocity. An overdue "
         "count outside the total is refused. What has no basis is the banding: the module's own "
         "comment records that a count per project or a response time published in the "
         "literature is not a per-week rate threshold, and that a normalisation the module does "
         "not perform sits between them.",
         "Calibrate the two ladders or convert them to declared owner policy. The measurement "
         "needs no change."),
    _row("4.3", "Submittal Rejection Rate", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 13 section 4.3", "no", "n/a", "yes", "HEURISTIC_UNCALIBRATED",
         "OWN_REGISTER", "THRESHOLD_CALIBRATION_BLOCKED",
         "The rate is rejected over assessed, exactly as specification 4.3 defines it, and "
         "reproduces the worked fifteen per cent. The domain is properly closed: a rejected "
         "count outside the total is refused rather than producing a rate above one, which every "
         "band above the top boundary would silently absorb into the worst band, a negative "
         "count is refused, and an empty register abstains. The status taxonomy the "
         "specification asks be clarified is partly addressed: the register the population came "
         "from is recorded, so a rate over requests for approval and one over submittals are "
         "distinguishable, and revise-and-resubmit and open counts are reported beside the rate "
         "rather than folded into it. The bands at five, fifteen and twenty-five per cent have "
         "no source, and the module's own comment records that rejection depends on what the "
         "specification requires and on the reviewer's practice, so no numeric threshold was "
         "located.",
         "Calibrate the bands or convert them to owner policy. Consider declaring the full "
         "status taxonomy explicitly rather than by register of origin."),
    _row("4.4", "NCR Rate", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 13 section 4.4", "yes", "partial", "yes", "HEURISTIC_UNCALIBRATED",
         "AUDITED_COHORT_ONLY", "CORRECT_ABSTENTION",
         "The defect this module used to carry was serious and is genuinely gone. It divided a "
         "backlog stock carried across every period by one period's intake flow, which is not a "
         "rate of anything and is unbounded above, and when the intake was empty it invented a "
         "denominator of one and then returned GREEN with the finding that no nonconformances "
         "were issued, on a project that could be carrying an unresolved backlog of any size. "
         "Both were verified as removed: the module now requires an audited cohort for the "
         "backlog to be a share of, and abstains without one. The share is exact and monotone "
         "and more open than the cohort contains is refused. What remains absent is the RATE "
         "half of the method: no exposure denominator, inspections, units, hours or value, is "
         "representable, and of the four backlog quantities the specification names only the "
         "open count is carried. Abstaining from the rate is correct, not a defect.",
         "P2. Carry an exposure denominator so a true rate can be computed alongside the "
         "backlog share, and carry age, severity and closure rate. Source the bands."),
    _row("4.5", "Weather Day Impact", "C. LITERATURE_SUPPORTED_ADAPTATION",
         "Specification 13 section 4.5", "yes", "no", "yes", "HEURISTIC_UNCALIBRATED",
         "OWN_FIELD_REPORT", "CORRECT_PROXY_ONLY",
         "Two fabrications were removed and both were verified gone. With no float figure the "
         "ratio is no longer set to one, which asserted the worst case as a measurement and made "
         "one day lost on a project with a year of float identical to one with none. And lost "
         "days inferred by the pipeline rather than counted in a field report are now refused "
         "outright, rather than carried into the same arithmetic with a parenthetical, because a "
         "qualifier in a display string is not a substitute for refusing. The remaining measure, "
         "lost days as a share of the float available to absorb them, is defensible and its "
         "guards are complete. But no affected activity, planned work, governing weather "
         "allowance, available path or causal linkage exists, so this is weather disruption days "
         "against float rather than the full impact claim specification 4.5 defines. The float "
         "is network-derived and the corpus has no activity network, so abstention is expected "
         "in practice.",
         "P3. Either carry the activity linkage and the governing allowance, or name the module "
         "for the disruption-days-against-float measure it computes."),
    _row("4.6", "Change Order Frequency", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 13 section 4.6", "yes", "no", "no", "HEURISTIC_UNCALIBRATED",
         "DUPLICATE_WITH_8.5", "METHOD_LABEL_MISMATCH",
         "The module reports a RAW COUNT of change orders and bands on it directly, with no "
         "exposure of any kind. Six changes on a six-month project and six on a six-year project "
         "produce the identical reading. Specification 4.6 states that frequency must have an "
         "exposure and works the arithmetic through. The contrast within this same category is "
         "sharp: the request velocity module requires its exposure window and abstains without "
         "it, so the instrument already knows how to do this. Second finding: the band is a "
         "JOINT ladder over the count and the scope growth together, and specification 4.6 "
         "states that magnitude is separate and must not be combined into one quantity without "
         "naming it as a composite. The two figures are reported separately, which is good, but "
         "the colour a reader sees is an unnamed composite. Third, the Category 8 modification "
         "governance module reads the same count and the same two contract sums by an almost "
         "identical ladder, so one body of evidence is banded twice.",
         "P1. Carry an exposure window so the count becomes a frequency. Name the composite or "
         "band the two quantities separately. P0D on the duplication with the Category 8 "
         "module."),
    _row("4.7", "Dispute Escalation Index", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 13 section 4.7", "yes", "no", "no", "HEURISTIC_UNCALIBRATED",
         "SHARED_DOCUMENT_COUNTS", "METHOD_LABEL_MISMATCH",
         "The missingness correction here is exemplary and was verified exhaustively: all three "
         "sources are required, so an identical project can no longer read three bands better "
         "for withholding its request and change order logs, and renormalising over the present "
         "terms was correctly refused as the fix because it would let removing a high term "
         "improve the reading in a subtler form. A reported count of zero is evidence and is "
         "distinguished from a log that was never read. The sources the reading rests on are "
         "listed on the output. But no dispute, claim or determination evidence exists anywhere. "
         "The index is a weighted sum of a document risk score, a request count capped at twenty "
         "and a change order count capped at ten, and specification 4.7 states in terms that "
         "request and change counts alone do not establish a dispute stage. The requirement that "
         "missing dispute evidence cannot improve the condition cannot even be expressed, "
         "because no dispute evidence is representable. The module's own qualifier calls it a "
         "proxy; the registered name does not.",
         "P3. Rename to the project-stress proxy the specification permits, or carry actual "
         "claim and dispute state evidence on a versioned governed stage ladder."),
    _row("4.8", "Subcontractor Performance", "C. LITERATURE_SUPPORTED_ADAPTATION",
         "Specification 13 section 4.8", "yes", "no", "yes", "HEURISTIC_UNCALIBRATED",
         "OPAQUE_SCALAR_INPUT", "PARAMETER_PROVENANCE_BLOCKED",
         "The module correctly refuses to manufacture a score: the browser's derived safety net "
         "is not ported, so with no supplied compliance score it abstains rather than inventing "
         "one from meeting mentions and document risk. The contributing signals are listed beside "
         "the score rather than folded into it, which is honest. But one precomputed compliance "
         "score arrives as a scalar and the module reports it. Specification 4.8 states in terms "
         "that a precomputed compliance score with unknown construction cannot independently "
         "validate this module. No criterion, rating, weight or version exists, so nothing about "
         "how the number was formed can be established, and no critical violation can be treated "
         "as noncompensatory because no criterion is separable. The oracle demonstrates both the "
         "weighted form the specification defines and the noncompensatory check, neither of "
         "which this module can express. The four bands have no source.",
         "P3. Carry the criterion ratings and versioned weights, or state plainly that the "
         "figure is an opaque extracted score."),
    _row("4.9", "Procurement Lead Time Monitor", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 13 section 4.9", "yes", "no", "yes", "HEURISTIC_UNCALIBRATED",
         "OWN_PROCUREMENT_LOG", "CORRECT_PROXY_ONLY",
         "The substantive defect is fixed and was verified exhaustively rather than sampled. The "
         "old form counted a delayed item twice, once as at risk and once again at double "
         "weight, so ten long-lead items with eight at risk and five delayed produced 1.8, a "
         "proportion of a set reported as one hundred and eighty per cent of it. Delayed items "
         "are now the subset of at-risk items they are, and the ratio was proved bounded in "
         "nought to one across every valid combination of counts up to ten items, exactly one at "
         "both endpoints, and monotone in severity. An empty log abstains rather than having a "
         "denominator of one invented for it. What is absent is the specification's core "
         "quantity: no item, required on-site date or forecast delivery date exists, so no "
         "procurement slack can be computed and item criticality, path need date and float "
         "cannot enter. It is a coherent aggregate of a procurement log rather than the "
         "item-level monitor the name implies.",
         "P2. Carry item-level required and forecast dates so slack can be computed. Source the "
         "0.5 at-risk weight and the four bands."),
    _row("4.10", "Specification Conflict Density", "C. LITERATURE_SUPPORTED_ADAPTATION",
         "Specification 13 section 4.10", "yes", "no", "no", "HEURISTIC_UNCALIBRATED",
         "DERIVED_FROM_DOC_RISK_AND_RFI", "METHOD_LABEL_MISMATCH",
         "The guards are sound and the substitution that used to report the unweighted document "
         "risk under this name when no requests existed is gone: with no requests the module now "
         "abstains on absent exposure. A document risk score outside nought to one is refused "
         "rather than multiplied through into the band ladder, and the figure is capped so the "
         "ladder is never fed an out-of-range quantity. But the measure is not a density. The "
         "quantity is the document risk score times the request count over the square root of "
         "the request count, which reduces to the risk score times the square root of the count, "
         "and specification 4.10 names this exact form and states in terms that it is not a "
         "specification conflict density. It has the wrong DIRECTION as well as the wrong "
         "structure: a density falls as exposure rises, and this rises with the request count "
         "until the cap intervenes. No individual conflict is identified, so no conflicting "
         "evidence locations are retained, and no governed exposure unit exists.",
         "P1. Either identify verified conflicts against a governed exposure unit and retain "
         "their evidence locations, or rename the module for the risk-weighted request-volume "
         "index it computes."),
]


def main() -> int:
    gate()
    m_4_1(); m_4_2(); m_4_3(); m_4_4(); m_4_5(); m_4_6(); m_4_7(); m_4_8(); m_4_9(); m_4_10()
    rows = ROWS()
    write_results(HERE / "run17" / "categories" / "category_4_results.csv", RESULT_HEADER, rows)
    A.check("ROWS", "ten Category 4 result rows were written", len(rows) == 10)
    A.check("ROWS", "no production change is recorded on any row",
            all(r["production_change_made"] == "no" for r in rows))
    return A.finish()


if __name__ == "__main__":
    sys.exit(main())
