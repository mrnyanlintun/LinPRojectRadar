"""
Run 19. Build the next remediation queue from the consolidated hundred-row table.

The owner's priority order, applied here:

  P0A  any defect in a VOTING module, or anything capable of changing participant or project
       status
  P0B  a method emitting a favourable or adverse result from scientifically invalid or missing
       evidence
  P0C  a regulatory or governance module making an overstated compliance or authority claim
  P0D  a Category 9 bypass, or lineage double counting
  P1   a canonical method implementation defect in non-voting analytical evidence
  P2   a missing canonical structure approved for implementation
  P3   calibration, threshold and parameter provenance; naming, proxy disclosure, category
       placement and parsimony
  FUTURE  experimental concept-only methods with no demonstrated incremental research value

THE QUEUE IS BUILT, NOT EXECUTED. Run 19 is an audit and repairs nothing.

Priority is assigned from the module's disposition and from an explicit per-module override
where the finding is more serious than its disposition alone implies, which is the case for
every P0B and P0C item. Each override names the reason, so nothing is promoted silently.
"""

from __future__ import annotations

import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RESULTS = HERE / "run17" / "scientific_results.csv"
OUT = ROOT / "code_audit" / "run19_next_remediation_queue.csv"

#: module_id -> (priority, one-line reason). Only entries whose priority is NOT implied by the
#: disposition alone appear here, and each says why it was placed where it is.
OVERRIDES: dict[str, tuple[str, str]] = {
    # P0B -- a favourable or adverse result from invalid or missing evidence.
    "9.2": ("P0B", "a document dated after the period cutoff reports a negative age and bands "
                   "Green, the freshest reading available, so a forward-dated or mistyped "
                   "document buys the best possible evidence-quality result"),
    "9.7": ("P0B", "a project whose last upload was seventeen months before the period cutoff "
                   "reports a ten day average interval and high frequency reporting, because "
                   "the cutoff is never compared to the last event and cessation is invisible"),
    "8.7": ("P0B", "two mentions of safety in meeting minutes become an incident rate of 20.0 "
                   "through an uncited multiplication by ten and band the project Red; the "
                   "specification forbids meeting minutes as an incidence-rate substitute in "
                   "those terms, and the zero case was closed while the non-zero case was not"),
    "3.7": ("P0B", "a negative analogous overrun percent bands Green with a negative money "
                   "exposure, and a negative budget at completion still reaches a Yellow band, "
                   "because neither input is guarded at all"),
    # P0C -- a regulatory or governance module making an overstated claim.
    "8.2": ("P0C", "an uncited twenty-five per cent threshold is presented to the reader as a "
                   "FAR Part 34 threshold and a reporting obligation is asserted with no "
                   "applicability determination of any kind"),
    "8.3": ("P0C", "the circular is reduced to a cost index below 0.90 and a budget above ten "
                   "million, which the specification forbids in terms, and the reader is told "
                   "mandatory reporting is triggered"),
    "8.4": ("P0C", "cost and schedule performance bands are published under a reporting "
                   "compliance name, so a contractor filing every report on time on a "
                   "struggling project reads as having breached a reporting threshold"),
    "10.3": ("P0C", "one rule is presented to the reader as a FAR threshold and is implemented "
                    "as a cost index above 0.80, with no provision cited"),
    # P0D -- Category 9 bypass and lineage double counting.
    "ARCH.1": ("P0D", "the Category 9 eligibility gate does not exist: the signal package is "
                      "marked unqualified and Categories 6, 7, 8 and 10 read raw values. The "
                      "bypass is disclosed on the data, which is materially better than a "
                      "hidden one, but the gate itself is absent"),
    "ARCH.2": ("P0D", "the evidence combination rule has no lineage argument, so one body of "
                      "evidence presented twice sharpens belief from 0.70 to 0.93. Latent "
                      "today because only one lineage votes, live the moment a second is "
                      "admitted"),
    "5.3": ("P0D", "tornado ranking recomputes its own impacts from the same evidence the "
                   "sensitivity module reads, by an incompatible definition, so a reader "
                   "seeing the two agree is seeing one reading counted twice"),
    "4.6": ("P0D", "the same change order count and contract sums are banded by both this "
                   "module and the Category 8 modification governance module"),
}

#: Disposition -> default priority, where no override applies.
BY_DISPOSITION = {
    "IMPLEMENTATION_DEFECT": ("P1", "a canonical method is represented and implemented "
                                    "incorrectly in non-voting analytical evidence"),
    "METHOD_LABEL_MISMATCH": ("P1", "the implementation performs a materially different method "
                                    "from the registered name"),
    "MISSING_CANONICAL_DATA_STRUCTURE": ("P2", "the method is legitimate but the implementation "
                                               "cannot represent the structure it needs"),
    "REGULATORY_VERSION_BLOCKED": ("P2", "the conformance rule cannot be evaluated against an "
                                         "identified versioned authority"),
    "PARAMETER_PROVENANCE_BLOCKED": ("P3", "the operator exists but its parameters lack "
                                           "defensible provenance"),
    "THRESHOLD_CALIBRATION_BLOCKED": ("P3", "the metric is correct but its operational "
                                            "thresholds have no source or calibration"),
    "METHOD_PASS_CALIBRATION_PENDING": ("P3", "the operator is correct and a tunable parameter "
                                              "or band still lacks calibration"),
    "CORRECT_PROXY_ONLY": ("P3", "a coherent transparent indicator published under a name that "
                                 "implies the stronger canonical method"),
    "OWNER_DECISION_REQUIRED": ("P3", "the literature permits alternatives and no governed "
                                      "choice has been made"),
    "FUTURE_RESEARCH_ONLY": ("FUTURE", "the formalism is testable but incremental value is not "
                                       "established and the module stays disabled"),
    "CORRECT_ABSTENTION": ("NONE", "the method correctly refuses because the required structure "
                                   "does not exist; no remediation is owed"),
    "SCIENTIFIC_PASS": ("NONE", "no material scientific deficiency was found"),
}

ORDER = ["P0A", "P0B", "P0C", "P0D", "P1", "P2", "P3", "FUTURE", "NONE"]


def main() -> int:
    rows = list(csv.DictReader(RESULTS.open(encoding="utf-8-sig")))
    out = []

    for r in rows:
        mid = r["module_id"]
        disp = r["scientific_disposition"]
        if mid in OVERRIDES:
            pri, why = OVERRIDES[mid]
        else:
            pri, why = BY_DISPOSITION[disp]
        # P0A: any defect in a voting module. Both voting modules passed, so this is empty, and
        # the rule is still applied rather than assumed.
        if r["voting_status"] == "voting" and disp not in ("SCIENTIFIC_PASS",
                                                           "CORRECT_ABSTENTION"):
            pri, why = "P0A", ("a defect in a module that votes on project status, which can "
                               "change what a participant is shown")
        if pri == "NONE":
            continue
        out.append({
            "priority": pri, "module_id": mid, "module_name": r["module_name"],
            "category": r["category"], "scientific_disposition": disp,
            "voting_status": r["voting_status"],
            "operational_activation": r["operational_activation"],
            "reason_for_priority": why,
            "required_action": r["required_next_action"],
            "finding_summary": r["finding_summary"],
        })

    # The two architecture-level items are not module rows and are added explicitly.
    for key in ("ARCH.1", "ARCH.2"):
        pri, why = OVERRIDES[key]
        out.append({
            "priority": pri, "module_id": key,
            "module_name": ("Category 9 qualification gate" if key == "ARCH.1"
                            else "Evidence lineage in the combination rule"),
            "category": "architecture", "scientific_disposition":
                "MISSING_CANONICAL_DATA_STRUCTURE",
            "voting_status": "n/a", "operational_activation": "n/a",
            "reason_for_priority": why,
            "required_action": ("Build the eligibility gate so a versioned qualified signal "
                                "package stands between project evidence and the categories "
                                "that consume it" if key == "ARCH.1" else
                                "Carry lineage on evidence and refuse to combine two "
                                "transforms of one body of evidence as independent sources"),
            "finding_summary": why,
        })

    out.sort(key=lambda r: (ORDER.index(r["priority"]), r["category"], r["module_id"]))
    cols = ["priority", "module_id", "module_name", "category", "scientific_disposition",
            "voting_status", "operational_activation", "reason_for_priority",
            "required_action", "finding_summary"]
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in out:
            w.writerow(r)

    from collections import Counter
    counts = Counter(r["priority"] for r in out)
    print(f"remediation queue: {len(out)} items")
    for p in ORDER:
        if counts.get(p):
            print(f"  {p}: {counts[p]}")
    print("\nP0 items in full:")
    for r in out:
        if r["priority"].startswith("P0"):
            print(f"  [{r['priority']}] {r['module_id']} {r['module_name']}")
            print(f"        {r['reason_for_priority']}")
    print(f"\nwritten: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
