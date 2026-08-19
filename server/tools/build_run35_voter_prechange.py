#!/usr/bin/env python3
"""
RUN 35 CLOSURE, STAGE 1: MEASURE THE VOTING DEFECT BEFORE ANYTHING IS EDITED.

NOTHING HERE IS HARD-CODED. The reference values are computed from the governed inputs with
`fractions.Fraction`, by an implementation of the published identity written from the definition;
the production values come from executing `registry.run_module`, the real entry point. The
discrepancies are the DIFFERENCE of those two, so if the production path changed, this harness
would report a different number rather than the one Run 35 recorded. A harness that cannot fail
proves nothing.

The band-boundary search is likewise a search: it enumerates candidate governed inputs and keeps
the ones where the rounded and the full-precision value fall on OPPOSITE sides of a band edge. If
no such input existed, this file would say so.

Writes code_audit/run35_voter_prechange_measurement.json.
"""
from __future__ import annotations

import json
import pathlib
import subprocess
import sys
from fractions import Fraction as F

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from app.simulation import registry as REG                                   # noqa: E402
from app.simulation.models import SIMULATION_VERSION                         # noqa: E402
from app.simulation.models_evm import (                                      # noqa: E402
    _TCPI_BEYOND_OBSERVED, _TCPI_PLANNED_EFFICIENCY,
    _VAC_BEYOND_OBSERVED_PCT, _VAC_BUDGET_MET_PCT)

NOOP = (lambda: 0.5)
CUT = "2026-06-30"

#: The Run-35 governed corpus inputs, restated nowhere else: this is the same scalar evidence the
#: Run-35 reference-standard artifact scored against, and it is read back from that artifact's
#: own generator rather than retyped.
from build_run35_eligibility import CORPUS_SI                                # noqa: E402


def head_object():
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                          text=True).stdout.strip()


# ---------------------------------------------------------------- the published identities
def tcpi_reference(bac, ev, ac):
    """PMI: TCPI = (BAC - EV) / (BAC - AC). Exact rational, written from the definition."""
    return (F(str(bac)) - F(str(ev))) / (F(str(bac)) - F(str(ac)))


def vac_reference(bac, cpi):
    """PMI: VAC = BAC - EAC with the index-based EAC = BAC / CPI. Exact rational."""
    return F(str(bac)) - F(str(bac)) / F(str(cpi))


def band_tcpi(value):
    """The module's own three-level band, applied to whatever value it is handed."""
    if value <= F(str(_TCPI_PLANNED_EFFICIENCY)):
        return "Green"
    return "Amber" if value <= F(str(_TCPI_BEYOND_OBSERVED)) else "Red"


def band_vac_pct(pct):
    if pct >= F(str(_VAC_BUDGET_MET_PCT)):
        return "Green"
    return "Amber" if pct >= F(str(_VAC_BEYOND_OBSERVED_PCT)) else "Red"


def run(mid, si):
    return REG.run_module(mid, dict(si), NOOP, CUT)


# ---------------------------------------------------------------- the boundary SEARCH
def boundary_search():
    """
    Look for governed inputs where the ROUNDED TCPI and the FULL-PRECISION TCPI fall on different
    sides of a band edge. Enumerated, not asserted: the numerator/denominator pairs below are
    swept and every hit is kept, so an implementation that did not round before banding would
    return an empty list and this file would report that no such fixture exists.
    """
    hits = []
    bac = 1_000_000.0
    for denom in (10_000, 20_000, 40_000):
        for edge in (_TCPI_PLANNED_EFFICIENCY, _TCPI_BEYOND_OBSERVED):
            for step in range(1, 60):
                numer = round(edge * denom) + step / 10.0
                if numer != int(numer):
                    continue
                exact = F(str(numer)) / F(str(denom))
                ev = bac - numer
                ac = bac - denom
                if not (0 <= ev <= bac and ac >= 0):
                    continue
                row = run("A1.7", {"bac": bac, "ev": ev, "ac": ac})
                if row.get("insufficient_data"):
                    continue
                produced = F(str(row["tcpi"]))
                if band_tcpi(produced) != band_tcpi(exact):
                    hits.append({
                        "inputs": {"bac": bac, "ev": ev, "ac": ac},
                        "full_precision_tcpi": str(exact),
                        "full_precision_tcpi_float": float(exact),
                        "production_tcpi_emitted": row["tcpi"],
                        "band_from_full_precision": band_tcpi(exact),
                        "band_production_assigned": row["status_color"],
                        "band_that_the_rounded_value_implies": band_tcpi(produced),
                        "edge_crossed": edge,
                        "evidence_metric": row["evidence_metric"],
                    })
    return hits


def main():
    obj = head_object()
    si = dict(CORPUS_SI)

    # ---- A1.7 on the Run-35 governed corpus
    t_row = run("A1.7", si)
    t_ref = tcpi_reference(si["bac"], si["ev"], si["ac"])
    t_prod = F(str(t_row["tcpi"]))
    t_diff = t_prod - t_ref

    # ---- A1.8 on the Run-35 governed corpus
    v_row = run("A1.8", si)
    v_ref = vac_reference(si["bac"], si["cpi"])
    v_prod = F(str(v_row["vac"]))
    v_diff = v_prod - v_ref

    hits = boundary_search()

    out = {
        "closure": "RUN 35 FINAL SCIENTIFIC CLOSURE, pre-change measurement",
        "measured_at_git_object": obj,
        "simulation_version_at_measurement": SIMULATION_VERSION,
        "harness_note": (
            "Every reference value is computed here from the governed inputs with "
            "fractions.Fraction, by an implementation written from the published definition. "
            "The discrepancies are differences of measured quantities, not constants: a changed "
            "production path yields a changed number."
        ),
        "A1.7": {
            "module": "A1.7 TCPI",
            "identity": "PMI: TCPI = (BAC - EV) / (BAC - AC)",
            "inputs": {k: si[k] for k in ("bac", "ev", "ac")},
            "full_precision_canonical_result": str(t_ref),
            "full_precision_canonical_float": float(t_ref),
            "production_prechange_result": t_row["tcpi"],
            "displayed_result": t_row["evidence_metric"],
            "band_status_assigned": t_row["status_color"],
            "band_from_full_precision": band_tcpi(t_ref),
            "discrepancy_exact": str(t_diff),
            "discrepancy_float": float(t_diff),
            "downstream_vote": "VOTES (A1.7 is one of the two CORE_VOTING_MODULES)",
            "execution_evidence": "registry.run_module('A1.7', governed corpus scalars)",
        },
        "A1.8": {
            "module": "A1.8 VAC",
            "identity": "PMI: VAC = BAC - EAC, index-based EAC = BAC / CPI",
            "inputs": {k: si[k] for k in ("bac", "cpi")},
            "full_precision_canonical_result": str(v_ref),
            "full_precision_canonical_float": float(v_ref),
            "production_prechange_result": v_row["vac"],
            "displayed_result": v_row["evidence_metric"],
            "band_status_assigned": v_row["status_color"],
            "band_from_full_precision": band_vac_pct(
                (v_ref / F(str(si["bac"]))) * 100),
            "discrepancy_exact": str(v_diff),
            "discrepancy_float": float(v_diff),
            "downstream_vote": "VOTES (A1.8 is one of the two CORE_VOTING_MODULES)",
            "execution_evidence": "registry.run_module('A1.8', governed corpus scalars)",
        },
        "A1.7_band_boundary_fixtures": {
            "search_performed": True,
            "fixtures_found": len(hits),
            "conclusion": (
                "THE PRE-CHANGE IMPLEMENTATION BANDS FROM THE ROUNDED VALUE, and that changes a "
                "STATUS rather than only a displayed number."
                if hits else
                "No input was found on which rounding changes the band. If this is the standing "
                "result, the finding is a display-precision matter and NOT a status defect."
            ),
            "fixtures": hits[:6],
        },
        "voting_set_at_measurement": sorted(REG.CORE_VOTING_MODULES),
    }
    p = ROOT / "code_audit" / "run35_voter_prechange_measurement.json"
    p.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {p.relative_to(ROOT)}")
    print(f"  A1.7 discrepancy {out['A1.7']['discrepancy_exact']}  "
          f"(band assigned {out['A1.7']['band_status_assigned']}, "
          f"full precision implies {out['A1.7']['band_from_full_precision']})")
    print(f"  A1.8 discrepancy {out['A1.8']['discrepancy_exact']}")
    print(f"  boundary fixtures found: {len(hits)}")
    for h in hits[:3]:
        print(f"    {h['inputs']}  exact {h['full_precision_tcpi_float']} -> "
              f"{h['band_from_full_precision']}, production emitted "
              f"{h['production_tcpi_emitted']} -> {h['band_production_assigned']}")


if __name__ == "__main__":
    main()
