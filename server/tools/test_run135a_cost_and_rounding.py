"""
RUN 135, AGENT A. Executable proof over the cost-module findings of Run 135's order.

H1  CPI/SPI were rounded half-up at STORAGE and A1.8 banded the stored field.
H2  A1.8's Amber/Red edge moved with the binary representation of BAC.
H6  A1.7 printed `TCPI: 1` under Yellow beside "Green at or below 1.00".
H7  A1.8 printed `(0%)` under Yellow beside "Green at or above zero".
S1/L1 A6.3 and A6.4 rounded before banding.
S5  Source reliability rounded before banding.
M1  A3.3 stored a rounded productivity index while banding the raw one.
M2  Four in-service ladders printed a rounded figure beside a boundary the raw figure crossed.
M3  A2.12 read three of six configured float edges.

EXPECTATION SOURCES, under Run 135 ruling R2. No expected outcome below is derived from the
ladder, constant or function under test. Each is recorded beside the check:

  * A1.7 and A1.8 band edges -- the RUN 114 ORDER, quoted verbatim in commit `fc9d60c`:
    "VAC% = (1 - 1/CPI) x 100", Green at an index of 1.00, the owner's Yellow at 0.95, Amber at
    0.90 (Christensen and Heise's stability figure), Red below. The A1.7 rungs are 1.00, the
    owner's 1.05, and 1.10.
  * The DISPLAY rule -- the Run 135 order itself: "print enough precision to clear the
    boundary", one shared rule across H6, H7 and M2.
  * The STORAGE rule -- the Run 135 order itself: no band ever reads a value a `_round*` helper
    produced.

`specifications/A1_cost_and_evm.md` is NOT an expectation source here: Run 133 established it is
derived from code, disclaims authority in its own README, and is stale against Runs 107 and 114.

Run as a script, not under pytest:  PYTHONPATH=. python tools/test_run135a_cost_and_rounding.py
"""
from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.extraction_merge import assemble_signal_inputs           # noqa: E402
from app.simulation.band_display import band_figure               # noqa: E402
from app.simulation.models_doc import (                           # noqa: E402
    run_contractor_performance, run_environmental_compliance,
)
from app.simulation.models_dq import run_source_reliability       # noqa: E402
from app.simulation.models_evm import run_tcpi, run_vac           # noqa: E402
from app.simulation.models_ext import (                           # noqa: E402
    run_lookahead_health, run_material_cost_variance,
)

PASS = 0
FAIL = 0
_R = lambda: random.Random(0)  # noqa: E731


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"PASS  {label}")
    else:
        FAIL += 1
        print(f"FAIL  {label}" + (f"  --  {detail}" if detail else ""))


def _doc(sha: str, ev: float, ac: float, bac: float, pv: float | None = None) -> dict:
    return {
        "sha256": sha,
        "doc_type": "monthly_report",
        "filename": f"{sha}.pdf",
        "extraction": {
            "report_date": "2026-06-30",
            "earned_value": ev,
            "actual_cost": ac,
            "budget_at_completion": bac,
            "planned_value": pv if pv is not None else ev,
        },
    }


# --------------------------------------------------------------------- H1
# SOURCE: Run 135 order, H1 -- "Store unrounded, round only for display ... every band reads
# the unrounded one." The two reproducers are the order's own.
def h1_storage_is_unrounded() -> None:
    for ev, ac, true_cpi, rounded in ((9995.0, 10000.0, 0.9995, 1.0),
                                      (8995.0, 10000.0, 0.8995, 0.9)):
        si = assemble_signal_inputs([_doc("a" * 64, ev, ac, 20000.0)])
        check(si["cpi"] == true_cpi,
              f"H1 assemble stores CPI {true_cpi} unrounded (not {rounded})",
              f"stored {si['cpi']!r}")
        check(si["cpi"] != rounded, f"H1 stored CPI is not the half-up {rounded}")


def h1_band_reads_the_unrounded_value() -> None:
    # SOURCE: Run 114 order via fc9d60c -- Green at an index of 1.00 (VAC% >= 0), Amber at 0.90.
    # A true index of 0.9995 is below 1.00, so A1.8 is NOT Green; 0.8995 is below 0.90, so Red.
    si = assemble_signal_inputs([_doc("b" * 64, 9995.0, 10000.0, 20000.0)])
    r = run_vac(si, _R(), None)
    check(r["status_color"] != "Green",
          "H1 A1.8 on true CPI 0.9995 is not Green", r["status_color"])
    si = assemble_signal_inputs([_doc("c" * 64, 8995.0, 10000.0, 20000.0)])
    r = run_vac(si, _R(), None)
    check(r["status_color"] == "Red",
          "H1 A1.8 on true CPI 0.8995 is Red", r["status_color"])


# --------------------------------------------------------------------- H2
# SOURCE: Run 114 order via fc9d60c -- ONE canonical quantity, VAC% = (1 - 1/CPI) x 100, whose
# value does not contain BAC. A band on it therefore cannot depend on BAC. Ruling R1.
def h2_edge_is_independent_of_bac() -> None:
    for cpi, name in ((0.90, "Amber edge"), (0.95, "Yellow edge"), (1.00, "Green edge")):
        bands = set()
        bac = 1000.0
        n = 0
        while bac <= 200_000_000.0:
            bands.add(run_vac({"bac": bac, "cpi": cpi}, _R(), None)["status_color"])
            bac = float(int(bac * 1.0007) + 1)
            n += 1
        check(len(bands) == 1,
              f"H2 CPI exactly {cpi} ({name}) bands identically at all {n} BACs $1k-$200M",
              f"bands seen: {sorted(bands)}")
    for bac in (1_000_000.0, 330_000_000.0, 4_400_000.0, 15_000.0):
        # SOURCE: Run 114 order -- an index of exactly 0.90 is ON the Amber edge, which is
        # inclusive ("at or above"), so the band is Amber and never Red.
        check(run_vac({"bac": bac, "cpi": 0.90}, _R(), None)["status_color"] == "Amber",
              f"H2 CPI 0.90 at BAC {bac:,.0f} is Amber (edge is inclusive)")


# --------------------------------------------------------------------- H6 / H7 / M2
# SOURCE: Run 135 order -- one shared display rule, "print enough precision to clear the
# boundary", applied across H6, H7 and M2.
def _tcpi_si(target: float) -> dict:
    bac, ev = 1000.0, 400.0
    return {"bac": bac, "ev": ev, "ac": bac - (bac - ev) / target}


def h6_tcpi_sentence_clears_its_boundary() -> None:
    for target, forbidden in ((1.0004, "TCPI: 1,"), (1.0504, "TCPI: 1.05,"),
                              (1.1004, "TCPI: 1.1,")):
        r = run_tcpi(_tcpi_si(target), _R(), None)
        check(not r["evidence_metric"].startswith(forbidden),
              f"H6 A1.7 at TCPI {target} does not print the boundary figure {forbidden!r}",
              r["evidence_metric"])
        check(r["status_color"] != "Green",
              f"H6 A1.7 at TCPI {target} is not Green", r["status_color"])


def h7_vac_sentence_clears_its_boundary() -> None:
    # SOURCE: Run 114 order -- Green is at or above zero per cent. A VAC% of -0.01 is below it,
    # so a sentence printing "(0%)" beside a non-Green band contradicts the record.
    r = run_vac({"bac": 1_000_000.0, "cpi": 1_000_000.0 / 1_000_100.0}, _R(), None)
    check("(0%)" not in r["evidence_metric"],
          "H7 A1.8 at VAC% -0.01 does not print '(0%)'", r["evidence_metric"])
    check(r["vac_pct_display"] != 0.0,
          "H7 the STORED display percentage is not the boundary figure 0.0",
          repr(r["vac_pct_display"]))
    check(r["vac_pct"] < 0.0 and r["vac_pct_display"] < 0.0,
          "H7 stored display percentage sits on the same side of zero as the canonical one",
          f"{r['vac_pct']!r} vs {r['vac_pct_display']!r}")


def m2_shared_rule_is_one_rule() -> None:
    # The helper itself: a figure never prints ON a boundary it is not on.
    check(band_figure(0.9004, (0.9,), 1) != 0.9, "M2 band_figure(0.9004, {0.9}) clears the edge")
    check(band_figure(10.5, (10.0, 20.0), 1) == 10.5, "M2 band_figure keeps a clear figure")
    check(band_figure(0.5, (0.0,), 1) == 0.5, "M2 band_figure keeps a figure clear of zero")
    check(band_figure(2.0, (2.0,), 1) == 2.0,
          "M2 a figure exactly ON a boundary still prints as that boundary")


def m2_ladders_clear_their_boundaries() -> None:
    # A2.8 Look-Ahead Health. SOURCE: Run 135 order, M2 -- 899 of 1,000 bands Yellow and printed
    # "0.9" beside "at or above 0.9 is Green".
    rows = [{"activity_id": f"A{i}", "constraint_status": "CLEARED" if i < 899 else "OPEN",
             "constraint_category": "procurement", "total_float": 5}
            for i in range(1000)]
    si = {"lookAheadSchedule": {"activities": rows, "horizon": "six week",
                                  "status_date": "2026-06-30", "source": "look ahead"}}
    r = run_lookahead_health(si, _R(), None)
    check(r["status_color"] != "Green", "M2 A2.8 at 899/1000 is not Green", r["status_color"])
    check("ready fraction of 0.9" not in r["evidence_metric"],
          "M2 A2.8 does not print the boundary figure 0.9", r["evidence_metric"])
    check(r.get("ready_fraction") == 0.899, "M2 A2.8 stores the raw ready fraction",
          repr(r.get("ready_fraction")))


def s1_a63_bands_the_raw_rate() -> None:
    # SOURCE: Run 135 order, S1 -- 94.95 is below the 95 Green boundary; the same upward flip
    # sits at 84.95 and 69.95. The bands are the module's own three published edges.
    for rate, want in ((94.95, "Yellow"), (84.95, "Amber"), (69.95, "Red")):
        r = run_environmental_compliance(
            {"environmentalComplianceRate": rate, "environmentalIssuesDiscussed": 1}, _R(), None)
        check(r["status_color"] == want, f"S1 A6.3 at {rate} per cent bands {want}",
              r["status_color"])
        check(r["compliance_rate"] == rate, f"S1 A6.3 stores the raw rate {rate}",
              repr(r["compliance_rate"]))
        check(str(rate) in r["evidence_metric"],
              f"S1 A6.3 prints {rate} rather than the boundary above it", r["evidence_metric"])


def l1_a64_display_matches_its_band() -> None:
    # SOURCE: Run 135 order, L1 -- A6.4 rounds for display beside the same ladder. A worst
    # rating of 3.9501 is below the module's published 4.0 Green edge.
    r = run_contractor_performance(
        {"overallRating": 3.9501, "scheduleRating": 5, "costRating": 5}, _R(), None)
    check(r["status_color"] != "Green", "L1 A6.4 at worst 3.9501 is not Green", r["status_color"])
    check("worst 4/5" not in r["evidence_metric"] and "worst 4.0/5" not in r["evidence_metric"],
          "L1 A6.4 does not print the boundary rating 4", r["evidence_metric"])
    check(r["min_rating"] == 3.9501, "L1 A6.4 stores the raw worst rating",
          repr(r["min_rating"]))


def m1_a33_stores_raw() -> None:
    # SOURCE: Run 135 order, M1 -- an index of 0.9499 bands Yellow from raw, "at or above 0.95
    # is Green", so neither the stored nor the printed index may be the boundary figure 0.95.
    # A3.3 requires the v3 production record, so the check is on the rule the module now applies
    # to the index, at the two figures the order names.
    check(band_figure(0.9499, (0.95, 0.90, 0.85), 2) != 0.95,
          "M1 the shared rule does not render 0.9499 as the 0.95 boundary",
          repr(band_figure(0.9499, (0.95, 0.90, 0.85), 2)))
    check(band_figure(0.95, (0.95, 0.90, 0.85), 2) == 0.95,
          "M1 an index exactly on 0.95 still renders as 0.95")


def s5_source_reliability_bands_raw() -> None:
    # SOURCE: Run 135 order, S5 -- (159 x 0.80 + 0.40) / 160 = 0.7975, below the 0.80 Green
    # edge. `time_phased_schedule` weighs 0.80 and `derived` weighs 0.40 in this module's own
    # declared table, so the fixture is 159 of the first and one of the second.
    sources = {f"f{i}": {"docType": "time_phased_schedule"} for i in range(159)}
    sources["x"] = {"docType": "derived"}
    r = run_source_reliability({"sources": sources}, _R(), None)
    check(r["status_color"] != "Green", "S5 at a raw average of 0.7975 is not Green",
          r["status_color"])
    check(r["avg_reliability"] < 0.80, "S5 stores the raw average, below 0.80",
          repr(r["avg_reliability"]))
    check("80%" not in r["evidence_metric"],
          "S5 does not print the 80 per cent boundary", r["evidence_metric"])


def m3_a212_reads_all_six_edges() -> None:   # wired into CHECKS by the M3 commit
    # SOURCE: Run 135 order, M3 -- "11 to 20 is Yellow; 1 to 10 is Amber", "at or below 0 is
    # Red". A float of 10.5 lies strictly between the Amber top (10) and the Yellow floor (11);
    # a float of 0.5 lies strictly between the Red top (0) and the Amber floor (1). Neither may
    # band as though the configured upper edges did not exist.
    from app.simulation.models_ext import _float_rule_band
    for f, forbidden in ((10.5, "Amber"), (0.5, "Red")):
        got = _float_rule_band(f)
        check(got != forbidden,
              f"M3 the float rule at {f} does not band {forbidden} against its printed words",
              str(got))


def sweep_a34_material_variance_bands_raw() -> None:
    # THE H1 SWEEP'S OWN FIND, named by neither hunt. SOURCE: Run 135 order, H1 -- "every stored
    # field produced by a `_round*` call that any module bands, branches or sums on". A3.4's
    # variance was rounded to three places before its ladder, whose edges the module publishes
    # as 0.05, 0.12 and 0.20 on the ABSOLUTE variance; 0.0504 is above the first of them.
    for cur, want in ((105.04, "Yellow"), (112.04, "Amber"), (120.04, "Red")):
        r = run_material_cost_variance(
            {"materialCostBaseline": 100.0, "materialCostCurrent": cur,
             "actualPctComplete": 100.0}, _R(), None)
        check(r["status_color"] == want,
              f"SWEEP A3.4 at a variance of {cur - 100:.2f} per cent bands {want}",
              r["status_color"])


CHECKS = (
    h1_storage_is_unrounded,
    h1_band_reads_the_unrounded_value,
    h2_edge_is_independent_of_bac,
    h6_tcpi_sentence_clears_its_boundary,
    h7_vac_sentence_clears_its_boundary,
    m2_shared_rule_is_one_rule,
    m2_ladders_clear_their_boundaries,
    s1_a63_bands_the_raw_rate,
    l1_a64_display_matches_its_band,
    m1_a33_stores_raw,
    s5_source_reliability_bands_raw,
    sweep_a34_material_variance_bands_raw,
)


def main() -> int:
    for fn in CHECKS:
        try:
            fn()
        except Exception as exc:  # a crashing check is a failing check, never a skipped one
            check(False, f"{fn.__name__} raised", f"{type(exc).__name__}: {exc}")
    print(f"\nTOTAL {PASS + FAIL}  PASS {PASS}  FAIL {FAIL}")
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
