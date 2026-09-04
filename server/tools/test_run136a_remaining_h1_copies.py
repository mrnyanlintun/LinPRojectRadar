"""
RUN 136 A. THE FOUR REMAINING COPIES OF H1, THE TWO ORPHAN BAND SETS, AND THE ONE BARE
SUPERSET ALIAS IN A DENOMINATOR.

Run 135's rounded-field sweep found four instances of the storage-time rounding defect that
nobody owned. Two are live and published bands (`models_fuzzy` B2.18 and B2.19), two are on the
training path (`training_engine`, `training_debrief`). This suite is the durable check that
they stay fixed, plus the checks for F7's removals and F8's alias.

EVERY EXPECTATION HERE IS INDEPENDENT OF THE IMPLEMENTATION UNDER TEST (R2). The bands are
recomputed from the ladder each site PRINTS on its own row -- 0.65 / 0.50 / 0.35 for the two
MCDM methods -- against the FULL-PRECISION score, computed here from the criteria the method
publishes rather than read back out of the module. The rounding rule the training layers must
agree with is `js_round`, which is `rng`'s, not `training_engine`'s. The alias expectations come
from the extraction contract's own sentence, quoted at each check.

Classification: ACTIVE QUALIFICATION TEST (R4). It fails on a real defect and is not a reader
of historical evidence.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TOTAL = 0
FAILED: list[str] = []


def check(cond: bool, label: str, detail: str = "") -> None:
    global TOTAL
    TOTAL += 1
    if cond:
        print(f"  PASS  {label}")
    else:
        FAILED.append(label)
        print(f"  FAIL  {label}  [{detail}]")


def section(title: str) -> None:
    print("\n" + "=" * 94)
    print(title)
    print("=" * 94)


# ---------------------------------------------------------------- the ladder, stated once here
MCDM_CUTS = (0.65, 0.50, 0.35)


def mcdm_band(score: float) -> str:
    """The ladder B2.18 and B2.19 print on their own rows. Restated here, not imported."""
    if score >= 0.65:
        return "Green"
    if score >= 0.50:
        return "Yellow"
    if score >= 0.35:
        return "Amber"
    return "Red"


def main() -> None:
    from app.simulation import models_fuzzy as mf
    from app.simulation.band_display import band_figure
    from app.simulation.rng import js_round

    r3 = lambda v: js_round(v * 1000) / 1000  # noqa: E731 -- the platform's half-up rule

    # ------------------------------------------------------------------------------- F1, B2.18
    section("F1. B2.18 MARCOS bands on the score, not on a rounded copy of it")

    def marcos_score(cpi: float, spi: float, doc: float) -> float:
        """The method's own published construction, recomputed here rather than imported.

        Criteria, ideals, anti-ideals and weights are the ones B2.18 states on its own rows.
        """
        crit = ((cpi, 1.05, 0.80, 0.40), (spi, 1.05, 0.80, 0.35), (1 - doc, 1.00, 0.30, 0.25))
        clamp = lambda v: min(1, max(0, v))  # noqa: E731
        s_p = sum(clamp(v / i) * w for v, i, _a, w in crit)
        s_a = sum(clamp(a / i) * w for _v, i, a, w in crit)
        s_i = sum(w for _v, _i, _a, w in crit)
        k_i, k_a = s_p / s_i, s_p / s_a
        d = k_i + k_a
        f_i, f_a = k_a / d, k_i / d
        return mf._jsdiv(d, 1 + mf._jsdiv(1 - f_i, f_i) + mf._jsdiv(1 - f_a, f_a))

    # The neighbourhood of every cut, and a wide sweep either side of it.
    bad = []
    near = 0
    for k in range(40001):
        cpi = 0.20 + (1.60 - 0.20) * k / 40000
        raw = marcos_score(cpi, 1.0, 0.2)
        if any(abs(raw - c) < 0.002 for c in MCDM_CUTS):
            near += 1
        got = mf.run_marcos({"cpi": cpi, "spi": 1.0, "docRiskScore": 0.2}, lambda: 0.5, None)
        if got["status_color"] != mcdm_band(raw):
            bad.append((cpi, raw, got["status_color"], mcdm_band(raw)))
    check(not bad,
          f"40,001 swept scores ({near} within 0.002 of a cut) band as the FULL-PRECISION "
          f"score does",
          str(bad[:3]))

    # The specific shape of the defect: `_round3` is half-up, so a score in [cut-0.0005, cut)
    # is lifted ONTO its own cut. Constructed at each cut from the ladder, not from the module.
    lifted = []
    for cut in MCDM_CUTS:
        raw = cut - 0.0004
        if r3(raw) >= cut and mcdm_band(raw) == mcdm_band(r3(raw)):
            lifted.append(cut)
    check(not lifted,
          "the constructed flip case at each cut -- cut minus 0.0004, which `_round3` lifts "
          "onto the cut -- is a genuine band flip, so this check can fail",
          str(lifted))

    # The printed figure never contradicts the band it was taken beside.
    contradicting = []
    for cut in MCDM_CUTS:
        for d in range(-800, 801):
            raw = cut + d * 1e-6
            if mcdm_band(band_figure(raw, MCDM_CUTS, 3)) != mcdm_band(raw):
                contradicting.append(raw)
    check(not contradicting,
          "4,803 figures around the three cuts print on the same side of every cut as the "
          "score itself",
          str(contradicting[:3]))

    # ------------------------------------------------------------------------------- F1, B2.19
    section("F1. B2.19 CRITIC-TOPSIS bands on the closeness coefficient itself")

    si = {"decisionMatrix": {"decision_object_id": "d1", "asset_version": "v1",
                             "split": "DEVELOPMENT", "evaluated_project_id": "p1",
                             "reference_member_project_ids": ["p2", "p3"]},
          "cpi": 1.0, "spi": 1.0, "docRiskScore": 0.1}
    original = mf.critic_topsis_decision
    topsis_bad = []
    swept = 0
    try:
        for cut in MCDM_CUTS:
            for d in range(-800, 801):
                raw = cut + d * 1e-6
                mf.critic_topsis_decision = (
                    lambda _obj, _c=raw: {"closeness": _c, "top_alternative": "A",
                                          "ranking": ["A"], "weights": {"w": 0.5},
                                          "alternatives": 2, "distance_ideal": 0.1,
                                          "distance_anti": 0.2})
                got = mf.run_critic_topsis(si, lambda: 0.5, None)
                swept += 1
                if got.get("status_color") != mcdm_band(raw):
                    topsis_bad.append((raw, got.get("status_color"), mcdm_band(raw)))
    finally:
        mf.critic_topsis_decision = original
    check(not topsis_bad,
          f"{swept} closeness coefficients around the three cuts band as the coefficient does",
          str(topsis_bad[:3]))

    # ------------------------------------------------------------------------ F2, the engine
    section("F2. the training engine hands the modules the ratio, not a rounded copy")

    from app.training_engine import (
        build_recommendation, initial_state, signal_inputs_from_state,
    )

    state = initial_state("A201-2017", 40_000_000.0, "normal")
    state["ac"], state["ev"], state["pv"] = 10_000_000.0, 8_995_100.0, 10_000_000.0
    state["bac"] = 40_000_000.0
    si2, _cut = signal_inputs_from_state(state)
    check(si2["cpi"] == state["ev"] / state["ac"],
          "signalInputs carry the cost index itself (ev/ac = 0.89951, which the old `_round3` "
          "handed on as 0.900 and B2.20 banded a rung high)",
          repr(si2["cpi"]))
    check(si2["spi"] == state["ev"] / state["pv"],
          "signalInputs carry the schedule index itself", repr(si2["spi"]))
    check(si2["actualPctComplete"] == state["ev"] / state["bac"] * 100,
          "signalInputs carry actual percent complete at full precision",
          repr(si2["actualPctComplete"]))
    check(si2["plannedPctComplete"] == state["pv"] / state["bac"] * 100,
          "signalInputs carry planned percent complete at full precision",
          repr(si2["plannedPctComplete"]))

    rec = build_recommendation(state)
    if rec is not None:
        check(rec["basis"]["cpi"] == state["ev"] / state["ac"],
              "the recommendation's recorded basis carries the ratio, not the printed figure",
              repr(rec["basis"]["cpi"]))
    else:
        check(True, "no recommendation is open at period 1; basis check not applicable")

    # ONE ROUNDING RULE PLATFORM-WIDE. `training_engine._round3` was Python `round`, half-to-
    # even; `rng.js_round` is half-up. SOURCE for the expectation: `rng.js_round`, which is what
    # `models_fuzzy`, `models_evm` and `extraction_merge` all use.
    from app.training_engine import _round3 as te_round3
    rule_bad = [v for v in (0.8995, 0.0005, 0.0015, 0.1235, 2.5005)
                if te_round3(v) != r3(v)]
    check(not rule_bad,
          "the training engine rounds a figure the same way the rest of the platform does "
          "(half-up, not half-to-even): 0.8995 prints 0.9 here as it does everywhere else",
          str([(v, te_round3(v), r3(v)) for v in rule_bad]))

    # ----------------------------------------------------------------------- F3, the debrief
    section("F3. the debrief prints its two ratios so a real difference still shows")

    from app.training_debrief import _spend_summary

    def st(ev: float, ac: float, pv: float) -> dict:
        return {"baseline_contract_sum": 1.0, "float_consumed_days": 0, "float_total_days": 0,
                "contingency_original": 0.0, "contingency_remaining": 0.0, "ac": ac, "ev": ev,
                "pv": pv, "owner_credibility": 3, "liquidated_damages_exposure": 0.0,
                "revised_contract_sum": 1.0}

    debrief_rule_bad = []
    for n in range(0, 20000, 7):
        ev = 8_000_000.0 + n
        summary = _spend_summary(st(ev, 10_000_000.0, 10_000_000.0))
        if summary["cpi"] != r3(ev / 10_000_000.0):
            debrief_rule_bad.append(ev)
    check(not debrief_rule_bad,
          "the debrief's cost index agrees with the platform's half-up rule on 2,858 ratios",
          str(debrief_rule_bad[:3]))

    hidden = []
    for d in range(1, 501):
        a, b = st(8_500_000.0, 10_000_000.0, 10_000_000.0), st(8_500_000.0 + d,
                                                               10_000_000.0, 10_000_000.0)
        if _spend_summary(a, against=b)["cpi"] == _spend_summary(b, against=a)["cpi"]:
            hidden.append(d)
    check(not hidden,
          "500 played/replayed pairs whose cost indices genuinely differ never print as the "
          "same figure -- the debrief exists to set one beside the other",
          str(hidden[:3]))

    plain = _spend_summary(st(8_500_000.0, 10_000_000.0, 10_000_000.0))
    check(plain["cpi"] == 0.85,
          "and an ordinary reading, with nothing near it, still prints at three decimals",
          repr(plain["cpi"]))

    # --------------------------------------------------------------------- F7, the orphans
    section("F7. the two true-orphan band sets are gone and pert_criticality_bands is not")

    from app.simulation import band_reference as BR
    for name in ("construction_frequency_band_cutoffs", "milestone_slip_ratio_bands"):
        check(BR.entry(name).get("configured") is False,
              f"{name} is no longer configured (nothing read it; removed at Run 136 F7)",
              str(BR.entry(name))[:120])
    check(BR.entry("pert_criticality_bands").get("configured") is True,
          "pert_criticality_bands IS still configured -- `tools/drive_run104.py:160` reads it "
          "to measure the Run 102 to 104 reversal",
          str(BR.entry("pert_criticality_bands"))[:120])

    # ------------------------------------------------------------------------ F8, the alias
    section("F8. `commitments_due` no longer accepts the bare heading `commitments`")

    from app.documents import _run69_structures

    class _NoEarlierPeriods:
        @staticmethod
        def scalars(_stmt):
            class _R:
                @staticmethod
                def all():
                    return []
            return _R()

    class _Project:
        id = 1

    def denoms(row: dict) -> dict:
        doc = {"doc_type": "inspection_report",
               "extraction": {"trade_denominators_json": [dict(row, Subcontractor="ACME")]}}
        out = _run69_structures(_NoEarlierPeriods(), _Project(), 3, [doc])
        rec = out.get("tradeAttributionRecords") or {}
        return (rec.get("denominators_by_subcontractor") or {}).get("ACME") or {}

    # SOURCE for this expectation, under R2: the extraction contract's own sentence, at
    # `app/extraction_client.py:696-698` -- "A different value sitting nearby, under a different
    # label, is never a substitute, even if it is a plausible value of the right type and in a
    # sensible range." A6.4's denominator is `commitments_due`, "firm COMMITMENTS DUE in the
    # reporting period" (`extraction_fields.py`). A column headed only "Commitments" states no
    # period and no status.
    d = denoms({"Commitments": 100, "Commitments Met On Time": 90})
    check("commitments_due" not in d,
          "a document printing only 'Commitments' reaches NOTHING in `commitments_due`, so "
          "A6.4 reads UNAVAILABLE rather than banding on an adjacent quantity",
          repr(d))
    check(d.get("commitments_met_on_time") == 90.0,
          "and the stated numerator heading is untouched", repr(d))
    for heading in ("Commitments Due", "Submittals Due", "RFIs Due", "Responses Due",
                    "Obligations Due"):
        got = denoms({heading: 100})
        check(got.get("commitments_due") == 100.0,
              f"the stated denominator heading still lands: {heading!r}", repr(got))

    print("\n" + "=" * 94)
    print(f"RESULT: {TOTAL - len(FAILED)}/{TOTAL} checks passed")
    print("=" * 94)
    if FAILED:
        for label in FAILED:
            print("  FAILED:", label)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
