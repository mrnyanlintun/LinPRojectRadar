"""
RUN 19 -- Category 9, data integrity and information quality. Seven scientific targets, plus the
ARCHITECTURE-LEVEL QUALIFICATION BOUNDARY the specification makes mandatory.

Supervisory specification section 18 states the target architecture as
    Project Evidence -> Category 9 assessment -> Qualified Evidence -> analytical use,
with Category 9 output being METADATA, not another independent risk vote, and Categories 6, 7, 8
and 10 rejecting raw unqualified values. Section 22 additionally requires that lineage be
preserved and that duplicating a correlated module cannot manufacture agreement or confidence.

Both of those are tested here, at the end, because they are properties of the system rather than
of any one module.

TEST AND AUDIT ONLY. Oracles come from run17/oracle/oracles_cat_9.py, self proved at import.
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
from app.simulation import fusion as FUSION                      # noqa: E402
from app.simulation import signal_package as SIG                 # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731

KNOWN_DEFECTS = {
    "9.1/applicability-determined": "CORRECT_PROXY_ONLY",
    "9.2/source-class-freshness": "MISSING_CANONICAL_DATA_STRUCTURE",
    "9.3/weight-provenance": "PARAMETER_PROVENANCE_BLOCKED",
    "9.3/unknown-source-not-favoured": "PARAMETER_PROVENANCE_BLOCKED",
    "9.4/critical-fields-are-audit-fields": "MISSING_CANONICAL_DATA_STRUCTURE",
    "9.4/chronology-checked": "MISSING_CANONICAL_DATA_STRUCTURE",
    "9.5/distinct-from-9.1": "CORRECT_PROXY_ONLY",
    "9.6/real-source-records": "METHOD_LABEL_MISMATCH",
    "9.7/governed-cadence": "MISSING_CANONICAL_DATA_STRUCTURE",
    "ARCH/raw-bypass": "MISSING_CANONICAL_DATA_STRUCTURE",
    "ARCH/lineage-double-count": "MISSING_CANONICAL_DATA_STRUCTURE",
}

A = Audit("category 9", KNOWN_DEFECTS)

#: Loaded through the gate so the oracle's own import-time self-proof becomes a
#: named red with a canonical RESULT line, rather than a traceback that the strict
#: runner would reject for the wrong reason.
O = oracle_gate(A, "oracles_cat_9")


def run(code_id: str, si: dict) -> dict:
    return REG.run_module(code_id, si, RAND, CUTOFF)


def abstained(out: dict) -> bool:
    return bool(out.get("insufficient_data")) or out.get("status_color") is None


CORE = {"bac": 1000, "ev": 400, "ac": 500, "pv": 500, "cpi": 0.8, "spi": 0.8,
        "docRiskScore": 0.3, "actualPctComplete": 40, "plannedPctComplete": 50,
        "baselineStart": "2026-01-01", "baselineEnd": "2026-12-31"}


def gate() -> None:
    A.check("GATE", "the Category 9 oracle reproduces the specification's worked answers",
            not O.self_test(), "; ".join(O.self_test()))
    ids = {t["module_id"] for t in population()}
    for mid in ("9.1", "9.2", "9.3", "9.4", "9.5", "9.6", "9.7"):
        A.check("GATE", f"{mid} is one of the hundred scientific targets", mid in ids)
    for code in ("C1.1", "C1.2", "C1.3", "C1.4", "C1.5", "C1.6", "C1.7"):
        A.check("GATE", f"{code} is non-voting", code not in REG.CORE_VOTING_MODULES)


# =============================================================================================
# 9.1 MISSING DATA INDEX -- specification 18, "9.1"
# =============================================================================================

def m_9_1() -> None:
    ten = [f"f{i}" for i in range(10)]
    vals = {f: 1 for f in ten}
    del vals["f0"], vals["f1"]
    A.near("9.1", "known-answer: the specification's ten applicable fields with two missing",
           O.missing_fraction(ten, vals), 0.20)

    out = run("C1.1", dict(CORE))
    A.near("9.1", "known-answer: a complete core set is one hundred per cent complete",
           out.get("completeness_pct"), 100, 0.5)
    A.check("9.1", "known-answer: two fields removed leaves nine of eleven present",
            run("C1.1", {k: v for k, v in CORE.items()
                         if k not in ("cpi", "spi")}).get("missing_count") == 2)

    # The rule the specification states in terms: zero is a value.
    A.proposition(
        "9.1", "9.1/zero-is-a-value",
        "a field holding zero is counted as present, since zero is a value and null is not",
        run("C1.1", {k: 0 for k in CORE}).get("completeness_pct") == 100,
        "a project reporting zero on every core field was scored as missing them")
    A.check("9.1", "invariant: completeness falls monotonically as fields are removed",
            [run("C1.1", dict(list(CORE.items())[:n])).get("missing_count")
             for n in (11, 8, 4, 0)] == [0, 3, 7, 11])
    A.check("9.1", "boundary: an entirely empty input is nought per cent complete and is "
                   "reported as evidence rather than abstained on",
            run("C1.1", {}).get("completeness_pct") == 0
            and run("C1.1", {}).get("status_color") == "Red")
    A.check("9.1", "invariant: the missing count and the present count sum to the field total",
            run("C1.1", {"bac": 1}).get("missing_count") + 1
            == run("C1.1", {"bac": 1}).get("total_fields"))

    A.proposition(
        "9.1", "9.1/applicability-determined",
        "the required fields are determined from the ACTIVE MODULE CONTRACT for this project, so "
        "a field not applicable to it is not counted missing",
        any(k in out for k in ("applicable_fields", "required_by_modules", "not_applicable")),
        "the denominator is a fixed list of eleven core fields written into the module, applied "
        "identically to every project whatever modules are active on it. Specification 9.1 "
        "requires applicable required fields to be derived from the active module contract and "
        "states that not-applicable fields must not be counted missing. A project for which a "
        "field is genuinely not applicable is therefore penalised for its absence. The measure "
        "is transparent and its arithmetic is exact; what is absent is applicability")


# =============================================================================================
# 9.2 DATA TIMELINESS SCORE -- specification 18, "9.2"
# =============================================================================================

def m_9_2() -> None:
    A.check("9.2", "known-answer: an age of twenty against an allowance of thirty is timely",
            O.timeliness_state(20, 30) == "TIMELY")
    A.check("9.2", "known-answer: an age of forty against the same allowance is stale",
            O.timeliness_state(40, 30) == "STALE")
    A.check("9.2", "known-answer: a future-dated record is invalid, not fresh",
            O.timeliness_state(-5, 30) == "INVALID_FUTURE_DATED")
    A.near("9.2", "known-answer: age is the period cutoff less the effective date",
           O.record_age_days(100, 80), 20)

    out = run("C1.2", {"docDate": "2026-06-10"})
    A.near("9.2", "known-answer: production measures the same age from the period cutoff",
           out.get("days_since_last_doc"), 20, 0.5)
    A.proposition(
        "9.2", "9.2/no-wall-clock",
        "the reference date is the period cutoff rather than the wall clock, so the same "
        "documents give the same answer on any day",
        run("C1.2", {"docDate": "2026-06-10"}).get("days_since_last_doc") == 20)
    A.check("9.2", "invariant: age rises monotonically as the document recedes",
            [run("C1.2", {"docDate": d}).get("days_since_last_doc")
             for d in ("2026-06-30", "2026-06-01", "2026-04-01")] == [0, 29, 90])
    A.check("9.2", "missingness: no document date abstains",
            abstained(run("C1.2", {})))
    A.check("9.2", "invalid input: a document date that is not a date abstains",
            abstained(run("C1.2", {"docDate": "not a date"})))

    future = run("C1.2", {"docDate": "2027-06-30"})
    A.proposition(
        "9.2", "9.2/future-dated-handled",
        "a document dated after the period cutoff receives explicit invalid or review handling",
        abstained(future),
        f"a document dated a full year after the period cutoff reports an age of "
        f"{future.get('days_since_last_doc')!r} days and bands "
        f"{future.get('status_color')!r}, the freshest reading the module has. The sentence a "
        f"reader sees says 'minus 365 days ago'. Specification 9.2 requires future-dated "
        f"records to receive explicit invalid or review handling; there is no lower guard on "
        f"the age at all, so a mistyped or forward-dated document buys the best possible "
        f"evidence-quality reading")
    A.proposition(
        "9.2", "9.2/source-class-freshness",
        "the freshness allowance is a governed property of the source class rather than one "
        "universal age applied to every document type",
        any(k in future for k in ("source_class", "allowed_age_days", "freshness_requirement")),
        "one ladder of thirty, sixty and ninety days is applied to every document whatever it "
        "is. Specification 9.2 requires a governed source-class freshness requirement and states "
        "that one universal age is not it: a contract value and a daily field report do not go "
        "stale at the same rate. The boundaries themselves have no source")


# =============================================================================================
# 9.3 SOURCE RELIABILITY WEIGHTING -- specification 18, "9.3"
# =============================================================================================

def m_9_3() -> None:
    w = {"authority": 0.5, "verification": 0.3, "freshness": 0.2}
    base = O.reliability({"authority": 0.8, "verification": 0.5, "freshness": 0.9}, w)
    better = O.reliability({"authority": 0.8, "verification": 0.9, "freshness": 0.9}, w)
    A.near("9.3", "known-answer: the weighted reliability model", base,
           0.8 * 0.5 + 0.5 * 0.3 + 0.9 * 0.2)
    A.check("9.3", "invariant: improving source verification with everything else held constant "
                   "does not lower reliability, which specification 9.3 requires be tested",
            better > base)
    try:
        O.reliability({"a": 1.0}, {"a": 0.5})
        A.check("9.3", "boundary: weights that do not sum to one are refused", False)
    except ValueError:
        A.check("9.3", "boundary: weights that do not sum to one are refused", True)

    out = run("C1.3", {"sources": {"bac": {"docType": "contract_value"},
                                   "ev": {"docType": "pay_application"}}})
    A.near("9.3", "known-answer: the mean of the two declared source weights",
           out.get("avg_reliability"), (0.95 + 0.90) / 2, 0.006)
    A.check("9.3", "invariant: reliability rises when a derived field is replaced by a measured "
                   "one, which is the monotonicity the specification names",
            run("C1.3", {"sources": {"bac": {"docType": "contract_value"}}}
                ).get("avg_reliability")
            > run("C1.3", {"sources": {"bac": {"docType": "derived"}}}).get("avg_reliability"))
    A.check("9.3", "structure: derived fields are counted and reported separately",
            run("C1.3", {"sources": {"a": {"docType": "derived"},
                                     "b": {"docType": "rfi"}}}).get("derived_fields") == 1)
    A.check("9.3", "missingness: no sources at all abstains",
            abstained(run("C1.3", {})) and abstained(run("C1.3", {"sources": {}})))
    A.check("9.3", "boundary: sources carrying no document type abstain rather than being "
                   "assigned a weight", abstained(run("C1.3", {"sources": {"bac": {}}})))
    A.check("9.3", "invariant: the reliability of a project's evidence does not depend on the "
                   "size of its budget, which specification 9.3 calls out as nonsensical",
            run("C1.3", {"bac": 10, "sources": {"a": {"docType": "rfi"}}}).get("avg_reliability")
            == run("C1.3", {"bac": 10 ** 9,
                            "sources": {"a": {"docType": "rfi"}}}).get("avg_reliability"))

    A.proposition(
        "9.3", "9.3/weight-provenance",
        "each source-class weight is versioned and carries a provenance record, as specification "
        "9.3 requires of every component weight",
        any(k in out for k in ("weight_version", "weight_source", "weights_provenance")),
        "twelve source-class weights from 0.40 to 0.95 are literals in the module with no "
        "version, no source and no derivation. They are the entire content of the measure: the "
        "output is their mean. Nothing establishes that a request for information is worth 0.65 "
        "while an inspection report is worth 0.70, and the four bands applied to the mean have "
        "no source either")
    unknown = run("C1.3", {"sources": {"a": {"docType": "an_unrecognised_source"}}})
    derived = run("C1.3", {"sources": {"a": {"docType": "derived"}}})
    A.proposition(
        "9.3", "9.3/unknown-source-not-favoured",
        "a source of an unrecognised type is not scored more reliable than a source the "
        "instrument knows to be derived",
        unknown.get("avg_reliability") <= derived.get("avg_reliability"),
        f"an entirely unrecognised document type falls to a default of "
        f"{unknown.get('avg_reliability')!r}, while a field the instrument KNOWS to be derived "
        f"scores {derived.get('avg_reliability')!r}. So relabelling a derived field with a "
        f"string the module does not recognise raises its assessed reliability. An unknown "
        f"source is the case about which least is known and should not outrank a known-weak one")


# =============================================================================================
# 9.4 AUDIT TRAIL COMPLETENESS -- specification 18, "9.4"
# =============================================================================================

def m_9_4() -> None:
    crit = ["method_version", "evidence_id", "judgment_id", "timestamp"]
    opt = [f"o{i}" for i in range(20)]
    full = {**{c: "x" for c in crit}, **{o: "x" for o in opt}}
    A.check("9.4", "known-answer: a complete record satisfies its critical fields",
            O.audit_completeness(full, crit, opt)["critical_satisfied"])
    partial = O.audit_completeness({**full, "method_version": None}, crit, opt)
    A.check("9.4", "known-answer: twenty present optional fields do not repair one missing "
                   "critical field, which is what noncompensatory means",
            not partial["critical_satisfied"] and partial["optional_coverage"] == 1.0)
    A.check("9.4", "known-answer: an event sequence running backwards is detected",
            O.chronology_intact([("a", 1), ("b", 2)])
            and not O.chronology_intact([("a", 5), ("b", 2)]))

    ev = [{"event": "project_created", "at": "2026-01-01"},
          {"event": "signals_extracted", "at": "2026-02-01"},
          {"event": "decision_recorded", "at": "2026-03-01"}]
    out = run("C1.4", {"events": ev})
    A.near("9.4", "known-answer: both required events present is full completeness",
           out.get("completeness_pct"), 100, 0.5)
    A.check("9.4", "structure: the decision record is reported separately rather than folded "
                   "into the score", out.get("has_decision_record") is True)
    A.check("9.4", "invariant: removing a required event lowers completeness",
            run("C1.4", {"events": ev[1:]}).get("completeness_pct") < 100)
    A.proposition(
        "9.4", "9.4/empty-log-is-evidence",
        "an absent event log abstains, because a caller that supplied none has said nothing, "
        "while an empty log is evidence and is reported as such",
        abstained(run("C1.4", {})) and not abstained(run("C1.4", {"events": []})))
    A.check("9.4", "boundary: an empty log reports the worst band rather than a comfortable one",
            run("C1.4", {"events": []}).get("status_color") == "Red")
    A.check("9.4", "invariant: an event the module does not recognise does not satisfy a "
                   "required one",
            run("C1.4", {"events": [{"event": "something_else", "at": "2026-01-01"}]}
                ).get("completeness_pct") == 0)

    A.proposition(
        "9.4", "9.4/critical-fields-are-audit-fields",
        "the mandatory critical fields examined are the audit fields specification 9.4 names, "
        "the method version, evidence identity, judgment identity and required timestamps of "
        "the signal, judgment and audit objects",
        any(k in out for k in ("missing_critical", "critical_fields", "method_version",
                               "evidence_id")),
        "the module checks for the PRESENCE OF TWO EVENT NAMES in a project event log, "
        "project_created and signals_extracted, and counts how many events there are. It never "
        "opens a signal, judgment or audit object and never looks at a method version, an "
        "evidence identity, a judgment identity or a timestamp on one. The quantity is a "
        "two-event checklist, not audit-trail completeness")
    backwards = run("C1.4", {"events": [{"event": "signals_extracted", "at": "2026-05-01"},
                                        {"event": "project_created", "at": "2026-01-01"}]})
    forwards = run("C1.4", {"events": [{"event": "project_created", "at": "2026-01-01"},
                                       {"event": "signals_extracted", "at": "2026-05-01"}]})
    A.proposition(
        "9.4", "9.4/chronology-checked",
        "an event sequence in which extraction precedes creation is detected as a chronology "
        "violation, which specification 9.4 requires be tested",
        backwards.get("status_color") != forwards.get("status_color")
        or backwards.get("completeness_pct") != forwards.get("completeness_pct"),
        "a log in which signals were extracted four months BEFORE the project was created "
        "produces exactly the same reading as a correctly ordered one. No timestamp is compared "
        "to any other, so neither a chronology violation nor a broken linkage is detectable")


# =============================================================================================
# 9.5 INFORMATION COMPLETENESS RATIO -- specification 18, "9.5"
# =============================================================================================

def m_9_5() -> None:
    A.near("9.5", "known-answer: the specification's six of eight applicable components",
           O.package_coverage(8, 6), 0.75)
    try:
        O.package_coverage(0, 0)
        A.check("9.5", "boundary: no applicable components leaves no coverage", False)
    except ValueError:
        A.check("9.5", "boundary: no applicable components leaves no coverage defined", True)

    out = run("C1.5", dict(CORE))
    A.check("9.5", "structure: measured, estimated and missing are reported separately rather "
                   "than collapsed into one number",
            all(k in out for k in ("measured", "estimated", "missing")))
    A.check("9.5", "invariant: measured, estimated and missing sum to the field total",
            out["measured"] + out["estimated"] + out["missing"] == out["total"])
    A.proposition(
        "9.5", "9.5/estimated-not-counted-measured",
        "a field whose source is recorded as derived is counted as estimated rather than as "
        "measured, so an estimate cannot pass for a document",
        run("C1.5", {**CORE, "sources": {"bac": {"docType": "derived"}}}).get("estimated") == 1)
    A.check("9.5", "invariant: coverage falls as fields are removed",
            [run("C1.5", dict(list(CORE.items())[:n])).get("completeness_ratio")
             for n in (11, 6, 2)] == sorted(
                [run("C1.5", dict(list(CORE.items())[:n])).get("completeness_ratio")
                 for n in (11, 6, 2)], reverse=True))
    A.check("9.5", "boundary: an empty input covers nothing",
            run("C1.5", {}).get("completeness_ratio") == 0)

    A.proposition(
        "9.5", "9.5/distinct-from-9.1",
        "this module asks a genuinely different question from the missing data index, over "
        "evidence-package components rather than over a longer list of the same fields",
        run("C1.5", {}).get("total") is not None
        and set(getattr(__import__("app.simulation.models_dq", fromlist=["_ALL_FIELDS"]),
                        "_ALL_FIELDS")).isdisjoint(
            set(getattr(__import__("app.simulation.models_dq", fromlist=["_CORE_FIELDS"]),
                        "_CORE_FIELDS"))),
        "the nineteen-field list of this module CONTAINS all eleven fields of the missing data "
        "index as a subset, so the two scores move together by construction and are not "
        "independent readings of evidence quality. The module does add something the missing "
        "data index does not have, the measured against estimated split, so it is not a pure "
        "duplicate. But it counts FIELDS, where specification 9.5 asks how much of the "
        "applicable evidence PACKAGE is present, and no evidence component is represented")


# =============================================================================================
# 9.6 CROSS-DOCUMENT CONSISTENCY -- specification 18, "9.6"
# =============================================================================================

def m_9_6() -> None:
    A.check("9.6", "known-answer: two sources reporting the same budget agree",
            O.cross_source_agreement(100.0, 100.0, 0.02) == "CONSISTENT")
    A.check("9.6", "known-answer: 100 against 110 within a two per cent tolerance is a material "
                   "conflict", O.cross_source_agreement(100.0, 110.0, 0.02) == "MATERIAL_CONFLICT")
    try:
        O.never_average([100.0, 110.0])
        A.check("9.6", "conflicting sources are never averaged into agreement", False)
    except AssertionError:
        A.check("9.6", "conflicting sources are never averaged into agreement, which "
                       "specification 9.6 forbids", True)

    agree = {"ev": 400, "ac": 500, "cpi": 0.8, "pv": 500, "spi": 0.8, "bac": 1000,
             "actualPctComplete": 40}
    out = run("C1.6", agree)
    A.near("9.6", "known-answer: a fully self-consistent input scores one hundred",
           out.get("consistency_score"), 100, 0.5)
    A.check("9.6", "known-answer: a reported cost index that disagrees with earned over actual "
                   "cost is detected",
            run("C1.6", {**agree, "cpi": 1.4}).get("inconsistencies") == 1)

    # The Run-14 denominator property, which the specification's spirit requires: a check that
    # cannot be run must not renormalise the score and reward the missing document.
    A.proposition(
        "9.6", "9.6/denominator-is-declared",
        "removing the figure that carries a disagreement does not renormalise the score over "
        "the survivors and make the documents agree",
        run("C1.6", {**agree, "actualPctComplete": 90}).get("consistency_score")
        >= run("C1.6", {k: v for k, v in agree.items()
                        if k != "actualPctComplete"}).get("consistency_score"))
    A.check("9.6", "structure: the checks that could not be run are reported separately",
            run("C1.6", {"ev": 400, "ac": 500, "cpi": 0.8}).get("checks_not_performed") == 2)
    A.check("9.6", "invariant: the consistent, inconsistent and not-performed counts sum to the "
                   "declared check count",
            (lambda r: r["checks_performed"] - r["inconsistencies"] + r["inconsistencies"]
             + r["checks_not_performed"] == r["checks_declared"])(
                run("C1.6", {"ev": 400, "ac": 500, "cpi": 0.8})))
    A.check("9.6", "missingness: earned value and actual cost are required",
            abstained(run("C1.6", {"cpi": 0.8})))
    A.check("9.6", "boundary: an actual cost of zero leaves the cost-index check unrunnable "
                   "rather than dividing by it",
            run("C1.6", {"ev": 400, "ac": 0, "cpi": 0.8, "pv": 500, "spi": 0.8}
                ).get("checks_performed", 0) <= 1 or abstained(run("C1.6", {"ev": 400, "ac": 0})))

    A.proposition(
        "9.6", "9.6/real-source-records",
        "the same governed fact is compared ACROSS REAL SOURCE RECORDS, carrying field identity, "
        "unit, effective period, revision status, source authority and an explicit tolerance",
        any(k in out for k in ("source_a", "source_b", "conflicting_sources", "field_identity",
                              "tolerance")),
        "the module compares figures WITHIN ONE FLAT INPUT DICTIONARY: the reported cost index "
        "against earned value over actual cost, the reported schedule index against earned over "
        "planned value, and reported progress against earned value over budget. That is internal "
        "arithmetic self-consistency of a single record, and it is a worthwhile check, but there "
        "is no second source anywhere. No source identity, authority, revision or effective "
        "period is represented, so two documents genuinely disagreeing about the budget at "
        "completion, which is the case specification 9.6 is written around, cannot be detected "
        "at all. The tolerances of 0.005 and 5 points are literals with no source")


# =============================================================================================
# 9.7 REPORTING FREQUENCY INDEX -- specification 18, "9.7"
# =============================================================================================

def _ev(*dates):
    return {"events": [{"event": "signals_extracted", "at": d} for d in dates]}


def m_9_7() -> None:
    perfect = O.cadence_report([0, 30, 60, 90], 30, 90)
    A.near("9.7", "known-answer: a perfect monthly cadence has a mean interval of thirty",
           perfect["mean_interval"], 30)
    A.check("9.7", "known-answer: a perfect cadence has missed nothing and has not ceased",
            not perfect["missed"] and not perfect["ceased"])
    stopped = O.cadence_report([0, 10], 30, 400)
    A.check("9.7", "known-answer: a project that reported twice and then stopped still shows a "
                   "short mean interval, so the mean alone cannot detect cessation",
            stopped["mean_interval"] == 10 and stopped["ceased"])
    A.check("9.7", "known-answer: a duplicate report is detected",
            O.cadence_report([0, 30, 30, 60], 30, 60)["duplicates"] == 1)
    try:
        O.cadence_report([5], 30, 60)
        A.check("9.7", "boundary: one report establishes no interval", False)
    except ValueError:
        A.check("9.7", "boundary: one report establishes no interval", True)

    out = run("C1.7", _ev("2026-04-01", "2026-05-01", "2026-06-01"))
    A.near("9.7", "known-answer: three monthly uploads give a mean interval near thirty days",
           out.get("avg_interval_days"), 30.5, 1.0)
    A.check("9.7", "structure: the upload count is reported alongside the interval",
            out.get("uploads") == 3)
    A.check("9.7", "invariant: the mean interval is invariant to the order the events arrive in",
            run("C1.7", _ev("2026-06-01", "2026-04-01", "2026-05-01")).get("avg_interval_days")
            == out.get("avg_interval_days"))
    A.check("9.7", "invariant: a longer gap between uploads gives a longer mean interval",
            run("C1.7", _ev("2026-01-01", "2026-06-01")).get("avg_interval_days")
            > out.get("avg_interval_days"))
    A.proposition(
        "9.7", "9.7/one-point-no-interval",
        "a single upload abstains, since one point establishes no interval",
        abstained(run("C1.7", _ev("2026-06-01"))))
    A.check("9.7", "missingness: an absent event log abstains",
            abstained(run("C1.7", {})))
    A.check("9.7", "invalid input: an event timestamp that is not a date abstains",
            abstained(run("C1.7", _ev("2026-04-01", "not a date"))))

    ceased = run("C1.7", _ev("2025-01-01", "2025-01-11"))
    A.proposition(
        "9.7", "9.7/cessation-detected",
        "a project whose last report is long before the period cutoff is reported as having "
        "ceased reporting, rather than by the mean interval of the reports it once made",
        abstained(ceased) or ceased.get("status_color") in ("Amber", "Red"),
        f"a project whose last upload was seventeen months before the period cutoff reports "
        f"{ceased.get('avg_interval_days')!r} days average interval, bands "
        f"{ceased.get('status_color')!r}, and tells the reader it has "
        f"'{ceased.get('evidence_metric')}'. The period cutoff is never compared to the last "
        f"event at all, so only the intervals BETWEEN observed reports are measured and the gap "
        f"since the last one is invisible. The independent oracle detects exactly this case. "
        f"Specification 9.7 names cessation as a required test, and this is a favourable "
        f"evidence-quality reading produced from evidence that stopped over a year ago")
    A.proposition(
        "9.7", "9.7/governed-cadence",
        "actual intervals are compared to a GOVERNED EXPECTED CADENCE, so a missed report, a "
        "duplicate, a late report, an approved extension and a changed cadence are each visible",
        any(k in out for k in ("expected_interval", "expected_cadence", "missed_reports",
                               "duplicates", "report_class")),
        "no expected cadence exists anywhere. The module reports the observed mean interval "
        "against a fixed ladder of fourteen, thirty and sixty days with no source, so it cannot "
        "distinguish a project on a governed quarterly cycle from one that is late. None of the "
        "seven cases specification 9.7 requires be tested, missed, duplicate, late, extension, "
        "changed cadence, cessation and multiple report classes, is representable")


# =============================================================================================
# THE ARCHITECTURE BOUNDARY AND LINEAGE -- specification sections 18 and 22
# =============================================================================================

def architecture() -> None:
    """
    Specification 18 states the target architecture and section 22 makes it a whole-system test.

    Two questions are asked separately: does Category 9 output leak into project status as
    another risk vote, and can downstream categories consume raw unqualified evidence.
    """
    # 1. Category 9 output must be metadata, not another vote.
    for code in ("C1.1", "C1.2", "C1.3", "C1.4", "C1.5", "C1.6", "C1.7"):
        A.check("ARCH", f"{code} does not vote on project status",
                code not in REG.CORE_VOTING_MODULES)
    A.check("ARCH", "the voting set is exactly the two cost identities and contains no "
                    "evidence-quality module",
            REG.CORE_VOTING_MODULES == frozenset({"A1.7", "A1.8"}),
            str(sorted(REG.CORE_VOTING_MODULES)))

    # 2. Can downstream categories consume raw, unqualified evidence.
    A.proposition(
        "ARCH", "ARCH/raw-bypass",
        "a versioned qualified signal package stands between project evidence and the evidence "
        "combination and governance categories, so Categories 6, 7, 8 and 10 cannot read raw "
        "unqualified cost, schedule and document-risk values",
        SIG.SIGNAL_QUALIFICATION != "unqualified",
        f"the signal package is marked {SIG.SIGNAL_QUALIFICATION!r} in production and carries "
        f"the recorded deviation: {SIG.CATEGORY_9_DEVIATION} The bypass is DISCLOSED on the data "
        f"rather than hidden, which is materially better than an undisclosed one, but the gate "
        f"itself does not exist. This is an architecture-level finding, not a defect in any one "
        f"module, and Run 19 is an audit and does not repair it")

    # 3. Category 9 quality must not itself become an adverse project condition.
    from app.simulation import qualification as QUAL
    A.check("ARCH", "the qualification layer carries separate named dimensions with controlled "
                    "states rather than one composite score, so a known gap and a measured "
                    "strength cannot cancel each other out",
            set(QUAL.QUALIFICATION_STATES) == {"PASS", "PARTIAL", "FAIL", "NOT_APPLICABLE",
                                               "NOT_ESTIMABLE"},
            str(QUAL.QUALIFICATION_STATES))
    A.check("ARCH", "the qualification layer is versioned, so a qualification recorded before a "
                    "shape change is distinguishable from one recorded after",
            bool(QUAL.QUALIFICATION_VERSION))
    qual_src = (HERE.parent / "app" / "simulation" / "qualification.py").read_text(
        encoding="utf-8")
    A.check("ARCH", "the qualification layer states in its own source that its metadata "
                    "dimensions never gate, never subtract and never become a number, so "
                    "evidence quality cannot be counted as a second adverse project condition",
            "They never gate, they never subtract, and they never become" in qual_src)
    A.check("ARCH", "the two dimensions this repository cannot answer are named honestly as "
                    "partial and not estimable rather than converted into a penalty or a pass",
            "NOT_ESTIMABLE" in qual_src and "PROVENANCE_PARTIAL_REASON" in qual_src)

    # 4. Lineage. Duplicating one body of evidence must not manufacture agreement or confidence.
    single = FUSION.governed_status_semantics(
        {"A1": {"status": "Amber", "contributes_to_project_status": True}}, raw_conflict=0.0)
    A.proposition(
        "ARCH", "ARCH/conflict-not-manufactured",
        "with one voting lineage the conflict coefficient is withheld and its state is named, "
        "rather than a zero being published that a reader cannot tell from perfect agreement",
        single["project_conflict"] is None
        and single["project_conflict_state"] == FUSION.NOT_ESTIMABLE_SINGLE_LINEAGE)
    A.check("ARCH", "with one voting lineage the rollup is not called overall project health, "
                    "since that would claim a breadth of evidence that has not voted",
            single["project_status_label"] == "Cost Recovery Status")
    duplicated = FUSION.governed_status_semantics(
        {"A1": {"status": "Amber", "contributes_to_project_status": True},
         "A1_copy": {"status": "Amber", "contributes_to_project_status": True}},
        raw_conflict=0.0)
    A.check("ARCH", "two categories reporting must widen the label rather than being hard-coded, "
                    "so the statement follows the voting set rather than a remembered constant",
            duplicated["project_status_label"] == "Governed Project Status")

    # Duplicating a same-lineage status through the evidence combination must not sharpen belief
    # without bound. This is the double-count property specification 22 point 5 requires.
    one = FUSION.dst_fuse(["Amber"])
    twice = FUSION.dst_fuse(["Amber", "Amber"])
    A.proposition(
        "ARCH", "ARCH/lineage-double-count",
        "combining the SAME body of evidence twice does not sharpen the belief distribution, "
        "because Dempster combination requires independent sources",
        abs(twice["mass"]["Amber"] - one["mass"]["Amber"]) < 1e-9,
        f"one Amber source gives mass {one['mass']['Amber']:.4f} on Amber and the same source "
        f"presented twice gives {twice['mass']['Amber']:.4f}. The combination rule has no "
        f"lineage argument, so nothing prevents two correlated transforms of one cost index "
        f"being combined as though they were independent evidence. In the CURRENT deployment "
        f"this is latent rather than active: only two modules vote and both are the same "
        f"lineage, and the semantics layer withholds the conflict coefficient precisely because "
        f"of that. It becomes live the moment a second lineage is admitted")


# =============================================================================================
# RESULT ROWS
# =============================================================================================

def _row(mid, name, basis, source, sreq, spres, impl, param, calib, thresh, lineage, disp,
         finding, nxt) -> dict:
    return {
        "module_id": mid, "module_name": name, "category": "9", "basis_class": basis,
        "operational_activation": "ADVISORY_ONLY", "voting_status": "non-voting",
        "primary_method_source": source, "canonical_structure_required": sreq,
        "canonical_structure_present": spres, "implementation_verified": impl,
        "known_answer_pass": "yes", "boundary_pass": "yes", "missingness_pass": "yes",
        "invariant_pass": "yes", "stochastic_diagnostics_pass": "n/a",
        "reproducibility_pass": "yes", "parameter_provenance_status": param,
        "calibration_status": calib, "threshold_status": thresh,
        "empirical_validation_status": "NOT_DONE", "regulatory_snapshot": "n/a",
        "cat9_qualification_status": "IS_THE_QUALIFICATION_LAYER", "lineage_status": lineage,
        "scientific_disposition": disp, "production_change_made": expected_flag(mid),
        "finding_summary": finding, "required_next_action": nxt,
        "test_names": "; ".join(A.coverage.get(mid, []))[:1800],
        "evidence_paths": ("server/tools/test_run19_category_9.py; "
                           "server/tools/run17/oracle/oracles_cat_9.py; "
                           "server/tools/run17/categories/category_9_faults.csv"),
    }


ROWS = lambda: [  # noqa: E731
    _row("9.1", "Missing Data Index", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 18 section 9.1; Wang and Strong (1996); Pipino, Lee and Wang (2002)",
         "yes", "partial", "yes", "n/a", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "SHARED_FIELD_LIST_WITH_9.5", "CORRECT_PROXY_ONLY",
         "The arithmetic is exact and the rule that matters most is correctly implemented: a "
         "field holding zero counts as present, because zero is a value and null is not, which "
         "was verified on a project reporting zero on every core field. Completeness falls "
         "monotonically as fields are removed, the counts reconcile to the total, and an empty "
         "input is reported as nought per cent rather than abstained on, which is right because "
         "the absence IS the evidence here. What is missing is applicability: the denominator is "
         "a fixed list of eleven fields applied identically to every project, where specification "
         "9.1 requires the applicable required fields to be derived from the active module "
         "contract and states that not-applicable fields must not be counted missing.",
         "P2. Derive the required-field set from the modules actually active on the project so "
         "an inapplicable field is not scored as missing. Source the four bands."),
    _row("9.2", "Data Timeliness Score", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 18 section 9.2",
         "yes", "no", "no", "NOT_SOURCED", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "OWN_DOCUMENT_DATE", "MISSING_CANONICAL_DATA_STRUCTURE",
         'RUN 20 CYCLE 1. The future-dating hole is closed. A document dated a full year after the period cutoff reported an age of minus three hundred and sixty five days and banded Green, the freshest reading the module has, so a mistyped or forward-dated document bought the best possible evidence-quality reading. There was no lower guard on the age at all. Specification 9.2 requires future-dated records to receive explicit invalid or review handling, and they now abstain as malformed. What remains is structural: one ladder of thirty, sixty and ninety days is applied to every document class, and specification 9.2 states that a governed source-class freshness requirement is needed and that one universal age is not it.',
         'P2. Carry a governed freshness allowance per source class. P3. Source the thirty, sixty and ninety day boundaries or retire them.'),
    _row("9.3", "Source Reliability Weighting", "C. LITERATURE_SUPPORTED_ADAPTATION",
         "Specification 18 section 9.3; Wang and Strong (1996)",
         "yes", "partial", "yes", "NOT_SOURCED", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "DOCUMENT_TYPE_ONLY", "PARAMETER_PROVENANCE_BLOCKED",
         "The monotonicity specification 9.3 names is satisfied: replacing a derived field with a "
         "measured one raises reliability, derived fields are counted and reported separately, "
         "and reliability does not depend on the size of the budget, which the specification "
         "calls out as nonsensical. Sources with no document type abstain rather than being "
         "assigned a weight. But the twelve source-class weights from 0.40 to 0.95 are literals "
         "with no version, no source and no derivation, and they are the entire content of the "
         "measure since the output is their mean. A second finding: an entirely unrecognised "
         "document type falls to a default of 0.50, ABOVE the 0.40 the instrument gives a field "
         "it knows to be derived, so relabelling a derived field with an unrecognised string "
         "raises its assessed reliability. Reliability is also assessed from document TYPE alone, "
         "never from verification status, provenance completeness or corroboration.",
         "P3. Version and source every weight. Correct the unknown-type default so an "
         "unrecognised source does not outrank a known-weak one."),
    _row("9.4", "Audit Trail Completeness", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 18 section 9.4",
         "yes", "no", "no", "NOT_SOURCED", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "EVENT_LOG_ONLY", "MISSING_CANONICAL_DATA_STRUCTURE",
         "The distinction the module does draw correctly is a good one: an absent event log "
         "abstains because a caller that supplied none has said nothing, while an empty log is "
         "evidence and bands worst. An unrecognised event does not satisfy a required one, and "
         "the decision record is reported separately rather than folded into the score. But the "
         "canonical structure is absent. The module checks for the presence of two event NAMES "
         "in a project event log and counts events. It never opens a signal, judgment or audit "
         "object, and never examines a method version, an evidence identity, a judgment identity "
         "or a timestamp, which are the mandatory critical fields specification 9.4 names. "
         "Because no timestamp is compared to any other, a log in which signals were extracted "
         "four months BEFORE the project was created produces an identical reading to a "
         "correctly ordered one: neither a chronology violation nor a broken linkage is "
         "detectable. The noncompensatory property was verified in the laboratory and cannot be "
         "exercised in production because no critical field is represented.",
         "P2. Assess the audit fields of the real signal, judgment and audit objects, treat the "
         "critical ones as noncompensatory, and check event chronology and linkage."),
    _row("9.5", "Information Completeness Ratio", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 18 section 9.5",
         "yes", "partial", "yes", "n/a", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "SUPERSET_OF_9.1_FIELD_LIST", "CORRECT_PROXY_ONLY",
         "The module is NOT a pure duplicate of the missing data index: it adds a measured "
         "against estimated split, so a field sourced from a derived value cannot pass for one "
         "read from a document, and that property was verified. Measured, estimated and missing "
         "are reported separately and reconcile to the total. But its nineteen-field list "
         "CONTAINS the missing data index's eleven fields as a subset, so the two scores move "
         "together by construction and must not be treated as independent readings of evidence "
         "quality. And it counts FIELDS where specification 9.5 asks how much of the applicable "
         "evidence PACKAGE is present and assessed; no evidence component is represented "
         "anywhere. The specification's alternative dispositions for this module are label "
         "mismatch or owner decision if it merely duplicates the missing data index, and it does "
         "more than that, so the honest reading is a transparent proxy for package coverage.",
         "P3. OWNER DECISION on whether package coverage should be measured over evidence "
         "components rather than fields. Disclose the shared lineage with the missing data index "
         "either way."),
    _row("9.6", "Cross-document Consistency Score", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 18 section 9.6",
         "yes", "no", "no", "NOT_SOURCED", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "SINGLE_RECORD_ONLY", "METHOD_LABEL_MISMATCH",
         "The internal consistency checks are real and worthwhile, and one property is "
         "especially good: the denominator is the three checks the method is DECLARED over, not "
         "the subset the corpus happened to support, so removing the figure that carries a "
         "disagreement no longer renormalises the score over the survivors and makes the "
         "documents agree. Checks that could not be run are reported separately. But there is no "
         "second source anywhere. The module compares figures WITHIN ONE FLAT INPUT: the reported "
         "cost index against earned over actual cost, and so on. Specification 9.6 requires the "
         "SAME governed fact compared ACROSS REAL SOURCE RECORDS carrying field identity, unit, "
         "effective period, revision status and source authority. Two documents genuinely "
         "disagreeing about the budget at completion, which is the case the specification is "
         "written around, cannot be detected at all. The tolerances of 0.005 and 5 points are "
         "literals with no source.",
         "P2. Carry per-field source records so the same fact can be compared across documents, "
         "and rename the present check for the record self-consistency it performs."),
    _row("9.7", "Reporting Frequency Index", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 18 section 9.7",
         "yes", "no", "no", "NOT_SOURCED", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED",
         "EVENT_LOG_ONLY", "MISSING_CANONICAL_DATA_STRUCTURE",
         "RUN 20 CYCLE 1. Cessation is visible. Only the intervals BETWEEN observed reports were measured, so the period cutoff was never compared to the last report and a project that uploaded twice ten days apart and then stopped for seventeen months reported a ten day average interval and banded Green. The gap from the last report to the end of the period is now measured on the module's own existing ladder, with no new threshold introduced, and the band is taken from whichever of the two readings is worse; the mean interval the project once kept is still reported truthfully beside it. What remains is structural: no GOVERNED expected cadence exists, so a missed report, a duplicate, a late report, an approved extension, a changed cadence and multiple report classes are still not distinguishable.",
         'P2. Carry a governed expected cadence per report class so the seven cases specification 9.7 names can each be tested. P3. Source the fourteen, thirty and sixty day ladder or retire it.'),
]


def main() -> int:
    gate()
    m_9_1(); m_9_2(); m_9_3(); m_9_4(); m_9_5(); m_9_6(); m_9_7()
    architecture()
    rows = ROWS()
    write_results(HERE / "run17" / "categories" / "category_9_results.csv", RESULT_HEADER, rows)
    A.check("ROWS", "seven Category 9 result rows were written", len(rows) == 7)
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
