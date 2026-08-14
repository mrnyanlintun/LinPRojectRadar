"""
RUN 20 CYCLE 8. THE ARCH.3 MATERIAL-INFLUENCE PROBE.

WHAT THIS ANSWERS AND WHAT IT REFUSES TO ANSWER. ARCH.3 was found by grouping modules by the
exact set of field names their preflight demands. That grouping is a QUESTION, never a verdict.
This probe answers the question the only way it can be answered: by moving one fact at a time
through the real production derivation and watching whether the module's emitted reading moves.

TWO DIFFERENT PROBES, BECAUSE THEY ANSWER TWO DIFFERENT QUESTIONS.

  PRIMITIVE PROBE. Move one PRIMITIVE governed fact, re-derive the cost and schedule indices the
  way `extraction_merge` derives them, and rerun. This is the probe whose answer is the module's
  evidence: it propagates through derived aliases exactly as production does. A module that never
  names the earned value but reads the cost index rests on the earned value, and this probe says
  so without anyone having to declare it.

  ALIAS PROBE. Hold every primitive fixed and move only the derived index. This does not
  establish evidence; it establishes whether the module reads the alias at all, which is what
  separates a field the preflight demands from a field the arithmetic uses.

WHY THE PRIMITIVE PROBE PROPAGATES AND THE PRE-FLIGHT SET DOES NOT. `extraction_merge` derives
cpi = ev/ac and spi = ev/pv, AND falls back to spi = actualPctComplete/plannedPctComplete when
the planned value is absent. The primitive set behind the schedule index is therefore NOT fixed
across projects. A field-name grouping cannot see that; a probe that re-derives can.

DISABLED MODULES ARE NOT PROBED AND GET NO DECLARATION. `run_module` short-circuits them before
any arithmetic. They emit no signal on any project, and a lineage record is a statement about a
signal's evidence. This is the A2.1 precedent from cycle 5 applied unchanged: declaring lineage
for a module that emits nothing asserts evidence that was never produced.

STOCHASTIC MODULES. The generator is a fixed constant sequence here, identical between the
baseline run and the perturbed run, so any movement observed is the fact's and not the draw's.

Output: code_audit/run20_cycle8_material_influence.csv
"""

from __future__ import annotations

import csv
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")))

from app.simulation.registry import (  # noqa: E402
    DISABLED_MODULES, activation_state, registry_index, run_module,
)

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(REPO, "code_audit", "run20_cycle8_material_influence.csv")

# The clusters ARCH.3 names, exactly as the register records them, plus the pair cycle 4 already
# declared, which is carried as the POSITIVE CONTROL: it is known dependent from cycle 4 and the
# probe must reach that verdict independently.
CLUSTERS: dict[str, tuple[str, ...]] = {
    "C1_bac_ev_ac_cpi": ("A1.11", "A1.3", "A3.6", "B3.2", "B4.2"),
    "C2_bac_two_indices": ("B3.4", "B4.3"),
    "C3_cpi_spi_doc": ("B2.10", "B2.11", "B2.14", "B2.15", "B2.16", "B2.18",
                       "B2.20", "B4.1", "B4.5", "B4.6"),
    "C4_two_indices": ("B2.12", "B2.13", "B2.17"),
    "C5_material_cost": ("A3.4", "A3.9"),
    "C6_contract_change_declared": ("A4.6", "B3.5"),
}

#: The primitive governed facts. A derived index is NOT here: it is not a fact.
PRIMITIVES: tuple[str, ...] = (
    "bac", "ev", "ac", "pv", "actualPctComplete", "plannedPctComplete", "docRiskScore",
    "materialCostBaseline", "materialCostCurrent", "changeOrderCount",
    "baselineContractSum", "revisedContractSum", "indirectCostPlan", "indirectCostActual",
    "rfiCount", "plannedLaborHours", "actualLaborHours",
)

#: A complete, non-degenerate project. Every figure is inside the domain every module states, so
#: an observed abstention is the module's arithmetic and never a missing input.
BASE_FACTS: dict[str, float] = {
    "bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
    "actualPctComplete": 40.0, "plannedPctComplete": 45.0, "docRiskScore": 0.30,
    "materialCostBaseline": 200_000.0, "materialCostCurrent": 214_000.0,
    "changeOrderCount": 6.0, "baselineContractSum": 900_000.0,
    "revisedContractSum": 963_000.0, "indirectCostPlan": 120_000.0,
    "indirectCostActual": 51_000.0, "rfiCount": 22.0,
    "plannedLaborHours": 8_000.0, "actualLaborHours": 8_600.0,
    "originalContingency": 80_000.0, "remainingContingency": 44_000.0,
    "analogousOverrunPct": 8.0, "totalFloat": 30.0, "consumedFloat": 12.0,
    "activitiesPlanned": 120.0, "activitiesConstrained": 18.0,
    "longLeadItemsTotal": 12.0, "longLeadAtRisk": 3.0, "longLeadDelayed": 1.0,
    "ncrIssued": 9.0, "ncrClosed": 5.0, "ncrOpen": 4.0, "weatherDaysLost": 4.0,
    "qualityDeficienciesNoted": 3.0, "safetyIncidentsDiscussed": 1.0,
    "environmentalIssuesDiscussed": 0.0, "overallRating": 3.0,
    "scheduleRating": 3.0, "costRating": 2.0,
}


def _round3(x: float) -> float:
    return round(x, 3)


def derive(facts: dict) -> dict:
    """THE PRODUCTION DERIVATION, reproduced from `extraction_merge` including the fallback.

    Reproduced rather than imported because the production function takes an observation set and
    a document fold, not a fact dictionary. The three lines that matter are copied verbatim in
    behaviour and the suite asserts they still agree with production.
    """
    si = dict(facts)
    ev, ac, pv = si.get("ev"), si.get("ac"), si.get("pv")
    si["cpi"] = _round3(ev / ac) if (ev is not None and ac not in (None, 0)) else None
    spi = _round3(ev / pv) if (ev is not None and pv not in (None, 0)) else None
    apc, ppc = si.get("actualPctComplete"), si.get("plannedPctComplete")
    if spi is None and apc is not None and ppc not in (None, 0):
        spi = _round3(apc / ppc)
    si["spi"] = spi
    return si


def _const_rng():
    """A constant generator. Identical between baseline and perturbation, so any movement seen is
    the fact's. It is not a scientific parameter and no band depends on it."""
    return 0.5


def reading(mid: str, si: dict):
    """THE MODULE'S WHOLE EMITTED RESULT, and not a hand-picked selection of keys.

    THE FIRST VERSION OF THIS FUNCTION WAS VACUOUS AND IS RECORDED AS SUCH. It compared
    `status_color`, `value`, `insufficient_data` and `finding`. No module in any of these
    clusters emits `value` or `finding` at all: they emit `posterior_eac`, `escalation_pct`,
    `probabilities`, `entropy` and their own metric strings. So the probe compared the BAND
    ALONE, and every dependence that moves a number without crossing a band boundary scored as
    absent. That is the same defect class as a guard that derives its expectation from the thing
    it is checking, and it is fixed by comparing the entire result rather than by adding the
    keys that were missed -- a hand-written key list is exactly what went wrong.

    Floats are rounded so that a last-bit difference from a different arithmetic ORDER, which is
    not a dependence, does not score as one. The rounding is at ten decimal places, far below any
    band boundary or reported figure, so it cannot hide a real movement.
    """
    try:
        r = run_module(mid, si, _const_rng, None)
    except Exception as exc:  # a crash is a reading too, and it is recorded, never swallowed
        return ("RAISED", type(exc).__name__, str(exc)[:120])
    return _canon(r)


def _canon(o):
    if isinstance(o, float):
        return round(o, 10)
    if isinstance(o, dict):
        return tuple(sorted((k, _canon(v)) for k, v in o.items()))
    if isinstance(o, (list, tuple)):
        return tuple(_canon(v) for v in o)
    return o


#: The perturbation ladder. Several multipliers, because one multiplier can land on a value that
#: happens to reproduce the baseline band, which would score a real dependence as absent.
LADDER = (0.55, 0.78, 1.22, 1.60)


def probe(mid: str) -> dict:
    base_si = derive(BASE_FACTS)
    base = reading(mid, base_si)
    material_primitives, material_aliases = [], []

    for p in PRIMITIVES:
        if BASE_FACTS.get(p) is None:
            continue
        moved = False
        for k in LADDER:
            facts = dict(BASE_FACTS)
            facts[p] = BASE_FACTS[p] * k
            if reading(mid, derive(facts)) != base:
                moved = True
                break
        if moved:
            material_primitives.append(p)

    # THE ALIAS PROBE. Every primitive held fixed; only the derived index moved. This is
    # deliberately an INCOHERENT state -- an index that does not equal ev/ac -- which is exactly
    # what makes it a control: a module that moves here reads the alias, and a module that does
    # not move here does not, whatever its preflight demands.
    for alias in ("cpi", "spi"):
        moved = False
        for k in LADDER:
            si = derive(BASE_FACTS)
            if si.get(alias) is None:
                continue
            si[alias] = _round3(si[alias] * k)
            if reading(mid, si) != base:
                moved = True
                break
        if moved:
            material_aliases.append(alias)

    return {"module_id": mid, "baseline": base,
            "material_primitives": material_primitives,
            "material_aliases": material_aliases}


def main() -> int:
    idx = registry_index()
    rows = []
    for cluster, mids in CLUSTERS.items():
        for mid in mids:
            state = activation_state(mid)
            if mid in DISABLED_MODULES:
                rows.append({
                    "cluster": cluster, "module_id": mid,
                    "module_name": idx[mid]["module_name"], "activation": state,
                    "preflight_required": "", "material_primitives": "",
                    "material_aliases": "", "baseline_reading": "NOT EXECUTED",
                    "verdict": "NO_SIGNAL_NO_DECLARATION",
                })
                continue
            r = probe(mid)
            rows.append({
                "cluster": cluster, "module_id": mid,
                "module_name": idx[mid]["module_name"], "activation": state,
                "preflight_required": "",
                "material_primitives": " ".join(r["material_primitives"]),
                "material_aliases": " ".join(r["material_aliases"]),
                "baseline_reading": str(r["baseline"])[:300],
                "verdict": "",
            })

    with open(OUT, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    for r in rows:
        print(f"{r['cluster']:28} {r['module_id']:6} {r['activation']:28} "
              f"prim=[{r['material_primitives']}] alias=[{r['material_aliases']}]")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
