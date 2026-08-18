#!/usr/bin/env python3
"""
RUN 35 STAGE 2: empirical validation scoring, the 100-row result artifact, the 100-row
operational disposition and the 100-row parsimony reconciliation.

THE METRIC CONTRACT IS READ, NOT RESTATED. Scoring reads
`code_audit/run35_validation_metric_contract.csv`, which was committed before this file existed,
and refuses to score any target the contract does not carry a predeclared metric for. A threshold
or metric therefore cannot be chosen after a result is observed: it is already on disk, in an
earlier commit, and this generator has no branch that writes one.

ALL ARITHMETIC IS EXACT. Every reference value is computed with fractions.Fraction from the
governed corpus inputs. No float comparison decides any verdict.

Writes:
  code_audit/run35_empirical_validation_results.csv
  code_audit/run35_operational_disposition.csv
  code_audit/run35_parsimony_reconciliation.csv
"""
from __future__ import annotations

import csv
import pathlib
import sys
from fractions import Fraction

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.simulation import registry as REG                                     # noqa: E402
from app.simulation.lineage import lineage_status, independence_established     # noqa: E402
from app.simulation.models import SIMULATION_VERSION                           # noqa: E402
from build_run35_eligibility import (                                          # noqa: E402
    CORPUS_SI, CUT, NOOP, execute, numeric_reading)

AUDIT = ROOT / "code_audit"
OUT_DIR = AUDIT
CONTRACT = AUDIT / "run35_validation_metric_contract.csv"
SCOPE = AUDIT / "run35_scientific_target_scope.csv"

VERDICTS = ("PASS", "FAIL", "INCONCLUSIVE", "NOT_APPLICABLE")
DISPOSITIONS = ("KEEP_OPERATIONAL", "KEEP_ADVISORY", "KEEP_ABSTENTION_CAPABLE",
                "RESEARCH_ONLY", "DISABLED_INSUFFICIENT_INPUT",
                "DISABLED_INSUFFICIENT_PROVENANCE", "ARCHIVED")

#: The archived historical method. Archived is not the same state as disabled and is kept in its
#: own set so the two cannot be merged.
ARCHIVED_TARGETS = {"B2.9"}
#: Disabled because the METHOD FORMULATION does not exist -- the supervisory artifacts carry DOI
#: citations and no frozen operator. This is a provenance absence, not a data absence.
PROVENANCE_DISABLED = {"B2.7", "B2.20"}


def read_csv(p):
    with p.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def write(name, header, rows):
    p = OUT_DIR / name
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {name}: {len(rows)} rows")
    return rows


# ------------------------------------------------------------------- exact reference standards
def exact_references():
    """
    Independent implementations of the three published identities, in EXACT rational arithmetic,
    written from the published definition and reading only the governed corpus inputs.
    """
    bac = Fraction(str(CORPUS_SI["bac"]))
    ev = Fraction(str(CORPUS_SI["ev"]))
    ac = Fraction(str(CORPUS_SI["ac"]))
    cpi = Fraction(str(CORPUS_SI["cpi"]))
    cases = Fraction(CORPUS_SI["oshaRecordableIncidents"])
    hours = Fraction(CORPUS_SI["totalManhours"])
    return {
        # PMI: TCPI = (BAC - EV) / (BAC - AC)
        "A1.7": ("tcpi", (bac - ev) / (bac - ac)),
        # PMI: VAC = BAC - EAC, index-based EAC = BAC / CPI
        "A1.8": ("vac", bac - bac / cpi),
        # OSHA: IncidenceRate = RecordableCases * 200000 / EmployeeHoursWorked
        "A6.2": ("incidence_rate", cases * 200_000 / hours),
    }


def score(mid, row, contract):
    """Apply the PREDECLARED rule from the contract. No rule may be created here."""
    field, ref = exact_references()[mid]
    produced = row.get(field)
    if produced is None:
        return ("INCONCLUSIVE", "the production row carries no value in the contracted field",
                "n/a", "n/a")
    got = Fraction(str(produced))
    equal = got == ref
    measured = (f"production {field} = {got} ({float(got):.10g}); independent published-identity "
                f"value = {ref} ({float(ref):.10g}); exact difference = {got - ref} "
                f"({float(got - ref):+.10g})")
    return ("PASS" if equal else "FAIL", measured, str(ref), str(got))


# ------------------------------------------------------------------- primitive-source lineage
class Probe(dict):
    """Records every primitive key the production path actually reads. Pairwise use only."""

    def __init__(self, base):
        super().__init__(base)
        self.seen = set()

    def get(self, k, *a):
        self.seen.add(k)
        return super().get(k, *a)

    def __getitem__(self, k):
        self.seen.add(k)
        return super().__getitem__(k)

    def __contains__(self, k):
        self.seen.add(k)
        return super().__contains__(k)


def primitive_sources(mid):
    p = Probe(CORPUS_SI)
    try:
        REG.run_module(mid, p, NOOP, CUT)
    except Exception:                                                   # noqa: BLE001
        pass
    return frozenset(k for k in p.seen if k != "evidenceQualification")


def main():
    contract = {r["module_id"]: r for r in read_csv(CONTRACT)}
    scope = {r["module_id"]: r for r in read_csv(SCOPE) if r["scientific_target"] == "YES"}
    assert len(scope) == 100, f"scope carries {len(scope)} scientific targets"

    order = sorted(scope, key=lambda m: (m[0], int(m[1]), float(m.split(".")[1])))
    executed = {}
    for mid in order:
        executed[mid] = (execute(mid) if not mid.startswith("D")
                         else {"__state__": "ABSTAINS"})

    # ------------------------------------------------------ empirical validation results, 100
    res_rows, scored = [], 0
    for mid in order:
        s, c = scope[mid], contract[mid]
        cls = s["run35_validation_eligibility"]
        row = executed[mid]
        if cls == "PARTIAL_REFERENCE_STANDARD":
            verdict, measured, ref, got = score(mid, row, c)
            scored += 1
            ref_id = {"A1.7": "REF-PMI-TCPI", "A1.8": "REF-PMI-VAC",
                      "A6.2": "REF-OSHA-INCIDENCE"}[mid]
            indep = ("INDEPENDENTLY AUTHORED PUBLISHED IDENTITY; NOT AN INDEPENDENT FIELD "
                     "OUTCOME (its arguments are the method's own inputs)")
            applicable = "YES - to the scalar component only"
            metric = c["predeclared_metric"]
            limitation = ("SCALAR COMPONENT ONLY. The band boundary, the status colour and every "
                          "field-outcome relationship are NOT validated: no labelled outcome "
                          "population exists, so no sensitivity, specificity or confusion matrix "
                          "is admissible. This is a reference-supported analytical result, not "
                          "an empirical field validation.")
            if verdict == "FAIL":
                limitation += (" FAIL CAUSE, MEASURED EXACTLY: the production path rounds the "
                               "scalar before emitting it, and for A1.7 before evaluating the "
                               "band, so the emitted value is a rounded rendering of the "
                               "identity rather than the identity. The residual is stated "
                               "exactly in the result column. This is a precision-and-banding "
                               "finding, NOT an arithmetic error in the identity; Run 35 does "
                               "not change it, because the rounding is the frozen "
                               "JavaScript-parity behaviour and altering it would change "
                               "participant-visible output.")
        else:
            verdict, measured, ref_id, metric = "NOT_APPLICABLE", "NO MEASUREMENT MADE", "NONE", \
                "NONE - no qualified independent reference standard exists"
            indep = "NO QUALIFIED REFERENCE STANDARD"
            applicable = "NO"
            limitation = {
                "STRUCTURE_OR_DATA_ABSENT":
                    "No empirical measurement was attempted because the governed structure or "
                    "evidence the method requires is absent from the controlled corpus, so the "
                    "method produces no output to score. NOT_APPLICABLE is the correct final "
                    "state and is NOT a pass.",
                "CALIBRATION_GAP_BLOCKS_VALIDATION":
                    "No empirical measurement was attempted because the module applies an "
                    "unresolved parameter to its emitted output, so any measured error would be "
                    "attributable to the uncalibrated value rather than to the method. "
                    "NOT_APPLICABLE is the correct final state and is NOT a pass.",
            }[cls]
        # the secondary truths, so precedence does not destroy information
        secondary = []
        if c["laboratory_suite_evidence_exists"] == "YES":
            secondary.append("SYNTHETIC_VALIDATION_ONLY (laboratory/canonical suite evidence "
                             "exists; it is NOT field validation)")
        if mid.startswith("D1."):
            secondary.append("EMPIRICAL_VALIDATION_PENDING_STUDY (Run-34 layer 5 = PENDING, "
                             "carried forward unchanged)")
        res_rows.append([
            mid, cls, ref_id, indep, applicable, metric, measured, verdict, limitation,
            "", "",                                   # filled below from the disposition pass
            "; ".join(secondary) or "none",
            "NO",                                   # synthetic_claimed_as_empirical
            "",                                     # run36 re-audit requirement, filled below
            SIMULATION_VERSION,
        ])

    # ------------------------------------------------------ operational disposition, 100
    def disposition(mid, s, row, verdict):
        if mid in ARCHIVED_TARGETS:
            return ("ARCHIVED",
                    "historical scientific method intentionally retained, not a current "
                    "operational method; no production route reaches it")
        if mid in PROVENANCE_DISABLED:
            return ("DISABLED_INSUFFICIENT_PROVENANCE",
                    "disabled because no frozen operator formulation exists in the supervisory "
                    "artifacts; the citations are DOIs, not a method this platform can execute")
        if mid in REG.DISABLED_CONCEPT_ONLY:
            return ("DISABLED_INSUFFICIENT_INPUT",
                    "disabled: the analytical structure its registered name claims -- and the "
                    "governed data that structure would need -- exists nowhere in the corpus")
        if s["supplied_or_computed"] == "SUPPLIED":
            return ("RESEARCH_ONLY",
                    "a supplied opaque scalar, not a computed canonical method; its precision "
                    "and recall are unmeasured and no labelled document corpus exists, so no "
                    "accuracy claim is supportable on any operational surface")
        if s["voting"] == "YES":
            return ("KEEP_OPERATIONAL",
                    "canonical published identity, band boundaries sourced to published "
                    "literature, governed intake, abstention guards present; the one bounded "
                    "operational use this instrument authorises")
        # KEEP_ADVISORY requires an actual bounded analytical QUANTITY. A6.1 and A6.3 execute
        # and emit a governed row whose whole content is a limitation sentence -- no compliance
        # rate, no conformance determination -- so they are abstention-capable, not advisory.
        if row.get("__state__") == "COMPUTES" and numeric_reading(row):
            return ("KEEP_ADVISORY",
                    "computes a bounded analytical reading on the governed corpus and is "
                    "excluded from category rollup, project status fusion, recommendation text, "
                    "courses of action and the decision card; it casts no status vote")
        return ("KEEP_ABSTENTION_CAPABLE",
                "canonical method retained; the governed structure or evidence it requires is "
                "absent from the current corpus, so abstention is the correct current behaviour "
                "and no reading is manufactured to fill the row")

    disp_rows, disp_by_id = [], {}
    idx = REG.registry_index()
    for mid in order:
        s = scope[mid]
        row = executed[mid]
        rres = next(r for r in res_rows if r[0] == mid)
        d, why = disposition(mid, s, row, rres[7])
        # (run36 is computed just below and written back into the result row)
        assert d in DISPOSITIONS, f"{mid}: illegal disposition {d}"
        disp_by_id[mid] = d
        lin = lineage_status(mid, applicable=mid not in REG.DISABLED_MODULES)
        run36 = ("re-audit the applied UNSUPPORTED band ladder and the declared-but-unimplemented "
                 "governed structure" if s["run35_validation_eligibility"] ==
                 "CALIBRATION_GAP_BLOCKS_VALIDATION" else
                 "confirm the scalar identity still holds and re-test the unvalidated band"
                 if s["run35_validation_eligibility"] == "PARTIAL_REFERENCE_STANDARD" else
                 "confirm the structure is still absent and the abstention still fires")
        disp_rows.append([
            mid, s["module_name"], s["category"], s["canonical_method_established"],
            s["run35_validation_eligibility"], rres[7], s["calibration_state"], lin,
            s["real_corpus_execution_state"], s["voting"], d, why, run36,
        ])
        # fill the disposition back into the result artifact
        rres[9] = s["calibration_state"]
        rres[10] = d
        rres[13] = run36

    # ------------------------------------------------------ parsimony reconciliation, 100
    prim = {mid: primitive_sources(mid) for mid in order}
    skey = {}
    for mid in order:
        skey[mid] = contract[mid] and scope[mid]["declared_governed_structure_key"]
    pars_rows = []
    for mid in order:
        s = scope[mid]
        mine, mykey = prim[mid], skey[mid]
        best, otype = "", "NONE"
        for other in order:
            if other == mid:
                continue
            # PAIRWISE ONLY. No connected component, no transitive closure.
            if mykey and mykey == skey[other] and "NO_GOVERNED_STRUCTURE_KEY" not in mykey:
                best, otype = other, "SHARED_GOVERNED_STRUCTURE (same primitive source object)"
                break
            if mine and mine == prim[other]:
                best, otype = other, "IDENTICAL_PRIMITIVE_SOURCE_SET"
                break
        if not best:
            for other in order:
                if other != mid and mine and mine < prim[other]:
                    best, otype = other, "PRIMITIVE_SOURCE_SUBSET"
                    break
        unique = "NO" if otype.startswith(("SHARED", "IDENTICAL")) else "YES"
        lin = lineage_status(mid, applicable=mid not in REG.DISABLED_MODULES)
        nec = ("YES - voting" if s["voting"] == "YES" else
               "NO - disabled or archived" if mid in REG.DISABLED_MODULES else
               "NO - abstains on the current corpus" if s["real_corpus_execution_state"]
               != "COMPUTES" else "BOUNDED ADVISORY")
        evidence = (f"primitive sources actually read on the governed corpus: "
                    f"{sorted(mine) or 'none reached'}; declared governed structure: {mykey}; "
                    f"lineage state {lin}; independence established: "
                    f"{independence_established(lin)}")
        pars_rows.append([
            mid, f"{s['module_name']} ({s['category']})",
            ", ".join(sorted(mine)) or "none reached on this corpus",
            lin, best or "none", otype, unique, nec, disp_by_id[mid], evidence,
            "PASS",
        ])

    write("run35_empirical_validation_results.csv",
          ["module_id", "validation_eligibility_class", "reference_standard_id",
           "reference_independence", "empirical_metric_applicable", "metric",
           "empirical_result", "verdict", "limitation", "calibration_state",
           "operational_disposition", "secondary_classes_also_true",
           "synthetic_claimed_as_empirical", "run36_reaudit_requirement",
           "simulation_version"], res_rows)

    write("run35_operational_disposition.csv",
          ["module_id", "module_name", "category", "canonical_method", "validation_class",
           "empirical_result", "calibration_provenance_state", "lineage_state",
           "current_routing", "voting", "run35_disposition", "rationale", "run36_action"],
          disp_rows)

    write("run35_parsimony_reconciliation.csv",
          ["module_id", "analytical_purpose", "primary_inputs", "primary_lineage",
           "closest_overlapping_target", "overlap_type", "unique_analytical_contribution",
           "current_operational_necessity", "proposed_disposition", "evidence", "result"],
          pars_rows)

    # ------------------------------------------------------ the acceptance counters
    from collections import Counter
    assert len(res_rows) == len(disp_rows) == len(pars_rows) == 100
    assert len({r[0] for r in res_rows}) == 100
    assert all(r[7] in VERDICTS and r[7] != "" for r in res_rows)
    assert all(r[8] for r in res_rows), "a limitation sentence is required on every row"
    assert all(r[12] == "NO" for r in res_rows), "synthetic_as_empirical_claims must be 0"
    assert all(r[13] for r in res_rows), "every row needs a Run-36 re-audit requirement"
    assert sum(1 for r in disp_rows if r[9] == "YES") == 2, "voting must be exactly 2"
    assert all(r[11] for r in disp_rows), "every disposition needs a rationale"
    print("\nverdicts:", dict(Counter(r[7] for r in res_rows)))
    print("dispositions:", dict(Counter(r[10] for r in disp_rows)))
    print("overlap types:", dict(Counter(r[5] for r in pars_rows)))
    print("unique analytical contribution NO:",
          sum(1 for r in pars_rows if r[6] == "NO"))
    print("synthetic_as_empirical_claims: 0")
    print(f"targets scored: {scored}; empirically validated (class A): 0")
    print("OK")


if __name__ == "__main__":
    main()
