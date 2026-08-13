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
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["module_id", "module_name", "cycle",
                                           "from_disposition", "to_disposition", "evidence"])
        w.writeheader()
        w.writerows(log)
    print(f"RESULT: {len(log)}/{len(TRANSITIONS)} transitions applied")


if __name__ == "__main__":
    main()
