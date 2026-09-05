"""
VERIFIES the Run-20 scientific reclassifications against server/tools/run17/scientific_results.csv
and writes the transition log, with its evidence, to code_audit/run20_disposition_transitions.csv.

This script does NOT edit the results table, and an earlier version of it did. The table is
rebuilt from the eight category result files by run19_consolidate.py, so anything written here
would have been silently overwritten the next time the consolidator ran, and a hand edit and a
regenerated file would have drifted apart without either one being wrong on its face. The
dispositions are therefore carried in the category suites, where the propositions that justify
them live, and this script only checks that the consolidated table says what the transition log
claims and fails if it does not.

Section 18 of the owner prompt: the same Run-19 vocabulary, no new positive labels, and every
transition cites the evidence that moved it. The transitions live in this file rather than in a
hand-edited CSV so the reason a module moved is versioned beside the move.
"""
from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
RESULTS = os.path.join(ROOT, "server", "tools", "run17", "scientific_results.csv")
OUT = os.path.join(ROOT, "code_audit", "run20_disposition_transitions.csv")

#: module_id -> (cycle, from, to, the fields to overwrite, the evidence for the move)
TRANSITIONS: dict[str, tuple] = {
    "3.7": (
        "1 P0B", "IMPLEMENTATION_DEFECT", "CORRECT_PROXY_ONLY",
        {"implementation_verified": "yes", "production_change_made": "yes",
         "finding_summary":
             "RUN 20 CYCLE 1. The invalid-evidence hole is closed: a budget at completion of "
             "zero or below now goes through the shared positive preflight and abstains on the "
             "invalid denominator instead of reaching a Yellow band, and no result reports a "
             "negative quantity of money at risk. Run 19's further instruction to refuse a "
             "NEGATIVE overrun percent was not adopted, and the reason is recorded rather than "
             "waived: field_registry.SIGNED_SI_FIELDS names analogousOverrunPct one of four "
             "fields where a negative value is a real project condition, because a reference "
             "project can underrun. The underrun is now reported as an underrun with no "
             "exposure carried, rather than as a negative exposure. What remains is the proxy "
             "finding the specification itself states: a single preloaded overrun percent with "
             "no analog selection, comparability criteria, normalisation or adaptation factors "
             "is only a proxy for analogous estimating.",
         "required_next_action":
             "P2 and P3. Carry identified analogs with comparability criteria and adaptation "
             "factors, or rename the module to the transparent indicator it is."},
        "server/tools/test_run20_p0b_evidence_domain.py, ten checks including two pinned "
        "historical defects and a mutation proof; server/tools/test_run19_category_3.py, "
        "proposition 3.7/domain-guarded amended and now holding"),
    "8.7": (
        "1 P0B", "IMPLEMENTATION_DEFECT", "MISSING_CANONICAL_DATA_STRUCTURE",
        {"implementation_verified": "yes", "production_change_made": "yes",
         "finding_summary":
             "RUN 20 CYCLE 1. The fabricated rate is gone. Two mentions of safety in meeting "
             "minutes became an incident rate of 20.0 through an uncited multiplication by ten "
             "and banded the project Red; specification 8.7 forbids using incidents discussed "
             "in meeting minutes as an OSHA incidence-rate substitute in those terms. The "
             "multiplier was removed at the root rather than fenced off in the derived case, so "
             "no incident COUNT from any document becomes a rate: only a reported incidence "
             "rate does. What remains is structural and is not a defect in the arithmetic. "
             "Employee hours worked is not an input, so the OSHA identity of recordable cases "
             "times two hundred thousand over hours worked cannot be evaluated, and no leading "
             "preventive indicator is representable, so the lagging and leading distinction "
             "OSHA guidance supports cannot be made. The benchmark of 3.0 remains uncited.",
         "required_next_action":
             "P2. Carry recordable cases and employee hours worked so the incidence-rate "
             "identity can be computed, and carry leading preventive indicators separately. "
             "P3. Source or retire the benchmark of 3.0."},
        "server/tools/test_run20_p0b_evidence_domain.py, ten checks including one pinned "
        "historical defect and a mutation proof; server/tools/test_run19_category_8.py, "
        "proposition 8.7/no-meeting-minute-substitute now holds and was retired from the "
        "register"),
    "9.2": (
        "1 P0B", "IMPLEMENTATION_DEFECT", "MISSING_CANONICAL_DATA_STRUCTURE",
        {"implementation_verified": "yes", "production_change_made": "yes",
         "finding_summary":
             "RUN 20 CYCLE 1. The future-dating hole is closed. A document dated a full year "
             "after the period cutoff reported an age of minus three hundred and sixty five "
             "days and banded Green, the freshest reading the module has, so a mistyped or "
             "forward-dated document bought the best possible evidence-quality reading. There "
             "was no lower guard on the age at all. Specification 9.2 requires future-dated "
             "records to receive explicit invalid or review handling, and they now abstain as "
             "malformed. What remains is structural: one ladder of thirty, sixty and ninety "
             "days is applied to every document class, and specification 9.2 states that a "
             "governed source-class freshness requirement is needed and that one universal age "
             "is not it.",
         "required_next_action":
             "P2. Carry a governed freshness allowance per source class. P3. Source the "
             "thirty, sixty and ninety day boundaries or retire them."},
        "server/tools/test_run20_p0b_evidence_domain.py, eight checks including one pinned "
        "historical defect and a mutation proof; server/tools/test_run19_category_9.py, "
        "proposition 9.2/future-dated-handled now holds and was retired from the register"),
    "9.7": (
        "1 P0B", "IMPLEMENTATION_DEFECT", "MISSING_CANONICAL_DATA_STRUCTURE",
        {"implementation_verified": "yes", "production_change_made": "yes",
         "finding_summary":
             "RUN 20 CYCLE 1. Cessation is visible. Only the intervals BETWEEN observed reports "
             "were measured, so the period cutoff was never compared to the last report and a "
             "project that uploaded twice ten days apart and then stopped for seventeen months "
             "reported a ten day average interval and banded Green. The gap from the last "
             "report to the end of the period is now measured on the module's own existing "
             "ladder, with no new threshold introduced, and the band is taken from whichever of "
             "the two readings is worse; the mean interval the project once kept is still "
             "reported truthfully beside it. What remains is structural: no GOVERNED expected "
             "cadence exists, so a missed report, a duplicate, a late report, an approved "
             "extension, a changed cadence and multiple report classes are still not "
             "distinguishable.",
         "required_next_action":
             "P2. Carry a governed expected cadence per report class so the seven cases "
             "specification 9.7 names can each be tested. P3. Source the fourteen, thirty and "
             "sixty day ladder or retire it."},
        "server/tools/test_run20_p0b_evidence_domain.py, thirteen checks including one pinned "
        "historical defect and a mutation proof; server/tools/test_run19_category_9.py, "
        "proposition 9.7/cessation-detected now holds and was retired from the register"),
    "8.2": (
        "2 P0C", "REGULATORY_VERSION_BLOCKED", "MISSING_CANONICAL_DATA_STRUCTURE",
        {"implementation_verified": "yes", "production_change_made": "yes",
         "threshold_status": "UNCITED_INTERNAL_REVIEW_LEVEL",
         "finding_summary":
             "RUN 20 CYCLE 2. The governance overclaim is closed. The reader was shown 'FAR "
             "Part 34: 17.6% overrun, threshold 25% (REPORTING REQUIRED)'. FAR 34.201 "
             "establishes earned value management policy and applicability and states no "
             "numeric cost-overrun threshold of any kind, so a regulation's name and part "
             "number had been attached to an uncited internal level; and a reporting obligation "
             "had been asserted from a cost ratio by a module that determines no applicability "
             "at all. Both are removed. The level is named an internal review level, its "
             "provenance is carried on the result, and the result records that no regulatory "
             "determination was made. The number was NOT moved and no substitute regulatory "
             "threshold was introduced, because none exists to introduce. The disposition "
             "leaves REGULATORY_VERSION_BLOCKED because the applicable authority IS established "
             "from the committed snapshot; what that authority establishes is that this "
             "module's threshold is not a regulatory one. What remains is structural: the "
             "acquisition designation, the agency, the agency procedure, the contract clauses, "
             "the award date and the rule version are not inputs, so none of the four "
             "applicability states can be reported.",
         "required_next_action":
             "P2. Carry the applicability evidence and report the four states. P3. Rename the "
             "module, which is registered under a regulation whose threshold it does not "
             "apply."},
        "server/tools/test_run19_category_8.py, proposition 8.2/threshold-is-regulatory now "
        "holds and was retired from the register, with three new checks on the renamed fields "
        "and one proving the bands did not move; mutation M7 restores the FAR attribution and "
        "turns the retired proposition red as an unrecorded defect"),
    "8.3": (
        "2 P0C", "REGULATORY_VERSION_BLOCKED", "MISSING_CANONICAL_DATA_STRUCTURE",
        {"implementation_verified": "yes", "production_change_made": "yes",
         "threshold_status": "UNCITED_INTERNAL_REVIEW_LEVEL",
         "finding_summary":
             "RUN 20 CYCLE 2. The asserted obligation is removed. Whenever the cost index fell "
             "below 0.90 on a budget of ten million or more the reader was told MANDATORY "
             "REPORTING TRIGGERED: a legal obligation asserted under a named federal circular "
             "on the strength of two uncited literals, by a check that evaluates none of the "
             "circular's requirements. Specification 8.3 states in terms that A-11 must not be "
             "reduced to budget, cost-index and progress thresholds. The conclusion is gone and "
             "the two observations remain, renamed for what they are; the conjunction, the "
             "boundaries and the band are unchanged, and the result now records that no "
             "regulatory determination was made. A separate defect was found by the same sweep "
             "and is carried forward rather than fixed here: the Yellow arm of the band "
             "requires a cost index simultaneously below 0.90 and at or above 0.92 and is "
             "therefore unreachable, so a four-value scheme bands on three.",
         "required_next_action":
             "P2. Represent each configured requirement with a rule identifier, section, "
             "applicability, required evidence, result and reviewer, and record the edition "
             "dated 2025-08-29. P1. Repair or retire the unreachable Yellow arm. P3. Rename "
             "the module, which is registered as a check against a circular it does not "
             "evaluate."},
        "server/tools/test_run19_category_8.py, three new checks on the renamed fields, the "
        "absence of the obligation and the unchanged boundaries, plus the sweep finding on the "
        "dead Yellow arm asserted over the whole index domain; mutation M8 restores MANDATORY "
        "REPORTING TRIGGERED and turns the obligation check red"),
    "8.4": (
        "2 P0C", "REGULATORY_VERSION_BLOCKED", "MISSING_CANONICAL_DATA_STRUCTURE",
        {"implementation_verified": "yes", "production_change_made": "yes",
         "threshold_status": "UNCITED_INTERNAL_REVIEW_LEVEL",
         "finding_summary":
             "RUN 20 CYCLE 2. The performance reading no longer presents itself as a reporting "
             "breach. Run 19 verified the consequence directly: a contractor submitting every "
             "required monthly report on time on a struggling project was reported as having "
             "BREACHED a reporting threshold, and one submitting nothing at all on a healthy "
             "project as within it. The three flags now name the comparison they make, a "
             "performance index below an internal review level of 0.90, the sentence carries no "
             "breach language, and the result states on its face that reporting compliance is "
             "not assessed here. The arithmetic, the guards, the conjunction and the bands are "
             "untouched. The disposition leaves REGULATORY_VERSION_BLOCKED because the "
             "authority is established from the committed snapshot, under which FAR 34.201(c) "
             "requires as a minimum monthly reports on contracts to which earned value "
             "management applies; what the module cannot do is represent any of it.",
         "required_next_action":
             "P2. Carry applicability, the contract clause, the required cadence or data item, "
             "the due date and the received date. P3. Rename the module, which measures "
             "performance under a reporting-compliance name."},
        "server/tools/test_run19_category_8.py, three new checks on the renamed fields, the "
        "absence of any compliance claim and the unchanged bands; mutation M9 restores the "
        "breach language and turns the compliance check red"),
    "10.3": (
        "2 P0C", "CORRECT_PROXY_ONLY", "CORRECT_PROXY_ONLY",
        {"production_change_made": "yes",
         "finding_summary":
             "RUN 20 CYCLE 2. One of the four rules was presented to the reader as 'FAR "
             "threshold (overrun < 25%)' and implemented as a cost index above 0.80. The "
             "arithmetic is self-consistent, since a forecast of budget over an index of 0.80 "
             "is a twenty-five per cent overrun, but no provision of the Federal Acquisition "
             "Regulation states such a threshold and none was cited. The rule is renamed for "
             "the forecast-overrun comparison it makes and no comparison changed, so the same "
             "projects violate the same rules. The disposition does not move: the module was "
             "and remains a coherent transparent four-rule feasibility set under a "
             "constraint-satisfaction name, which is the finding the specification itself "
             "states for it. What cycle 2 removed was a governance overclaim carried inside it.",
         "required_next_action":
             "P3. Rename the module to the transparent feasibility rule set it is, or build "
             "variables, domains and a search. The four rule thresholds remain unsourced."},
        "server/tools/test_run19_category_10.py, proposition "
        "10.3/no-regulatory-label-on-a-performance-threshold now holds and was retired from the "
        "register, with a new check proving the renamed rule fires on the same projects; "
        "mutation M10 restores the FAR rule name and turns the retired proposition red as an "
        "unrecorded defect"),
}


def main() -> None:
    rows = list(csv.DictReader(open(RESULTS, encoding="utf-8")))
    log = []
    for r in rows:
        t = TRANSITIONS.get(r["module_id"])
        if not t:
            continue
        cycle, want_from, want_to, updates, evidence = t
        assert r["scientific_disposition"] == want_to, (
            f"{r['module_id']} reads {r['scientific_disposition']} in the consolidated results "
            f"table, but this transition log claims it now reads {want_to}. The category suite "
            f"and the transition log disagree; neither is edited to make them agree, the "
            f"disagreement is the finding.")
        assert r["production_change_made"] == "yes", (
            f"{r['module_id']} moved disposition but records no production change")
        log.append({"module_id": r["module_id"], "module_name": r["module_name"],
                    "cycle": cycle, "from_disposition": want_from, "to_disposition": want_to,
                    "evidence": evidence})

    assert len(log) == len(TRANSITIONS), "a declared transition matched no module row"
    with open(artifact_out(OUT), "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["module_id", "module_name", "cycle",
                                           "from_disposition", "to_disposition", "evidence"])
        w.writeheader()
        w.writerows(log)
    print(f"RESULT: {len(log)}/{len(TRANSITIONS)} transitions applied")


if __name__ == "__main__":
    main()
