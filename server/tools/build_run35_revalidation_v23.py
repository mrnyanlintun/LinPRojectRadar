#!/usr/bin/env python3
"""
RUN 35 CLOSURE, SECTION 8: re-execute the three partial reference standards through the CORRECTED
production route, and record the v22 and v23 results side by side.

THE ORIGINAL FAILURES ARE NOT ERASED. The v22 column is READ OUT OF the committed Run-35 result
artifact, which is left exactly as Run 35 wrote it; this file adds the successor result beside it.

The acceptance rule is the one the closure's owner decision bounds: equality with the published
identity EVALUATED IN THE ARITHMETIC THE APPLICATION ALREADY USES, tolerance zero. The residual
against an infinitely precise rational is reported separately and descriptively, because it is
IEEE-754 representation and not a rounding the implementation chose.

Writes code_audit/run35_partial_reference_revalidation_v23.csv.
"""
from __future__ import annotations
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402

import csv
import pathlib
import sys
from fractions import Fraction as F

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from app.simulation import registry as REG                              # noqa: E402
from app.simulation.models import SIMULATION_VERSION                    # noqa: E402
from build_run35_eligibility import CORPUS_SI                           # noqa: E402

AUDIT = ROOT / "code_audit"
NOOP = (lambda: 0.5)
CUT = "2026-06-30"

TARGETS = {
    "A1.7": ("tcpi", "REF-PMI-TCPI", "(BAC - EV) / (BAC - AC)",
             lambda s: (s["bac"] - s["ev"]) / (s["bac"] - s["ac"]),
             lambda s: (F(str(s["bac"])) - F(str(s["ev"])))
             / (F(str(s["bac"])) - F(str(s["ac"])))),
    "A1.8": ("vac", "REF-PMI-VAC", "BAC - BAC / CPI",
             lambda s: s["bac"] - s["bac"] / s["cpi"],
             lambda s: F(str(s["bac"])) - F(str(s["bac"])) / F(str(s["cpi"]))),
    "A6.2": ("incidence_rate", "REF-OSHA-INCIDENCE", "cases * 200000 / hours",
             lambda s: s["oshaRecordableIncidents"] * 200000 / s["totalManhours"],
             lambda s: F(s["oshaRecordableIncidents"]) * 200_000 / F(s["totalManhours"])),
}


def historical_v22():
    """The Run-35 result rows, read from the artifact Run 35 committed. Not retyped."""
    with (AUDIT / "run35_empirical_validation_results.csv").open(encoding="utf-8") as fh:
        return {r["module_id"]: r for r in csv.DictReader(fh)}


def main():
    hist = historical_v22()
    si = dict(CORPUS_SI)
    rows = []
    verdicts = {}
    for mid, (field, ref_id, identity, float_ref, exact_ref) in sorted(TARGETS.items()):
        row = REG.run_module(mid, dict(si), NOOP, CUT)
        produced = row.get(field)
        app_ref = float_ref(si)
        exact = exact_ref(si)
        # THE PREDECLARED RULE, unchanged in form from Run 35: exact equality, tolerance zero.
        # What is compared is the identity evaluated in the application's own arithmetic, which
        # is the precision the owner's decision bounds this closure to.
        verdict = "PASS" if produced == app_ref else "FAIL"
        verdicts[mid] = verdict
        residual = F(str(produced)) - exact
        rows.append([
            mid, ref_id, identity,
            hist[mid]["verdict"], hist[mid]["empirical_result"][:200], "sim-2026.08-v22",
            verdict,
            f"production {field} = {produced!r}; identity in the application's arithmetic = "
            f"{app_ref!r}; difference = {F(str(produced)) - F(str(app_ref))}",
            SIMULATION_VERSION,
            str(residual), f"{float(residual):+.3e}",
            "IEEE-754 double representation of the exact rational; NOT a rounding the "
            "implementation applies, and no decimal precision was invented to remove it",
            "SCALAR COMPONENT ONLY. The band, the status and every field-outcome relationship "
            "remain unvalidated: no labelled outcome population exists. This is a "
            "reference-supported analytical result, NOT an empirical field validation.",
        ])
    p = AUDIT / "run35_partial_reference_revalidation_v23.csv"
    with artifact_out(p).open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["module_id", "reference_standard_id", "published_identity",
                    "v22_verdict_original_run35", "v22_measurement_original_run35",
                    "v22_simulation_version", "v23_verdict", "v23_measurement",
                    "v23_simulation_version", "residual_against_exact_rational",
                    "residual_float", "residual_cause", "limitation"])
        w.writerows(rows)
    print(f"wrote {p.relative_to(ROOT)}: {len(rows)} rows")
    for r in rows:
        print(f"  {r[0]}: v22 {r[3]} -> v23 {r[6]}   ({r[7][:90]})")
    assert verdicts["A6.2"] == hist["A6.2"]["verdict"], "A6.2 must be unchanged"
    print(f"\nA6.2 unchanged: {verdicts['A6.2']} at both lines")
    print("empirically FIELD-validated targets: 0 (unchanged; a published identity is not a "
          "field outcome)")


if __name__ == "__main__":
    main()
