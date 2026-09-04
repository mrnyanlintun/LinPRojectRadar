"""RUN 133. The executable band contract for A1.6, A1.7, A1.8, A1.9, A3.2 and A3.5.

This is the AUDIT'S evidence, not a change. It pins, by executing the modules themselves on
constructed inputs, exactly which bands the running instrument asserts and on which side of each
boundary, so that any future divergence between the written specification and the executable
constants is caught by a failing check rather than by reading.

Run as a script with cwd = server/. Pure functions only: no model call, no database.
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from app.simulation import models_evm as E
from app.simulation import models_ext as X

ok = fail = 0


def check(label, got, want):
    global ok, fail
    if got == want:
        ok += 1
        print(f"  PASS  {label}: {got!r}")
    else:
        fail += 1
        print(f"  FAIL  {label}: got {got!r}, expected {want!r}")


def tcpi_band(v):
    """Solve for inputs giving exactly TCPI == v, then band by running the module."""
    bac, ac = 1000.0, 500.0          # remaining budget 500
    ev = bac - v * (bac - ac)        # remaining work = v * 500
    r = E.run_tcpi({"bac": bac, "ev": ev, "ac": ac}, lambda: 0.5, None)
    return r.get("status_color"), r.get("tcpi")


def vac_band(cpi):
    """Drive A1.8 by the cost performance index itself. The percentage is an EXACT restatement
    of the index -- VAC% = (1 - 1/CPI) x 100 -- so an index boundary is a percentage boundary
    exactly, and no float round-trip is introduced by the check itself."""
    r = E.run_vac({"bac": 1000.0, "cpi": cpi}, lambda: 0.5, None)
    return r.get("status_color"), r.get("vac_pct")


print("=== A1.7 TCPI: the ladder the code executes ===")
for v, want in ((1.00, "Green"), (1.0001, "Yellow"), (1.05, "Yellow"), (1.0501, "Amber"),
                (1.10, "Amber"), (1.1001, "Red")):
    check(f"TCPI {v}", tcpi_band(v)[0], want)
check("A1.7 Yellow rung constant", E._TCPI_OWNER_YELLOW, 1.05)
check("A1.7 Green edge constant", E._TCPI_PLANNED_EFFICIENCY, 1.00)
check("A1.7 Amber edge constant", E._TCPI_BEYOND_OBSERVED, 1.10)
# RUN 35's STANDING RULING: the band comes off the full-precision value, never a rounded one.
# 1.0004 rounds to 1.0 at three places; if the band read the rounded value it would say Green.
_c, _raw = tcpi_band(1.0004)
check("A1.7 bands full precision, not _round3", (_c, E._round3(_raw)), ("Yellow", 1.0))

print("=== A1.8 VAC: the ladder the code executes ===")
_Y = E._VAC_OWNER_YELLOW_PCT          # -5.263157894736842
_A = E._VAC_BEYOND_OBSERVED_PCT       # -11.11111111111111
# NOTE THE 0.95 ROW. It is MEASURED, not intended. See the RUN 133 FINDING below: the module
# reaches the Yellow edge by a DIFFERENT arithmetic path from the one the constant is built by,
# so at an index of exactly 0.95 the computed percentage falls a few units in the last place
# BELOW the edge and the reading is Amber rather than Yellow. This check pins what the running
# instrument actually does so the defect cannot be lost.
for cpi, want in ((1.0, "Green"), (0.99999999, "Yellow"), (0.95, "Amber"),
                  (0.9499999, "Amber"), (0.90, "Amber"), (0.8999999, "Red")):
    _col, _pct = vac_band(cpi)
    check(f"VAC at CPI {cpi} (= {_pct:.10f} pct)", _col, want)
check("A1.8 CPI 1.00 is exactly 0.00 per cent", vac_band(1.0)[1], 0.0)
# ===================== RUN 133 FINDING: A FLOATING-POINT BOUNDARY DEFECT ON A1.8 ============
# The Yellow edge constant is built as (1 - 1/0.95) * 100. The module builds its percentage as
# ((BAC - BAC/CPI) / BAC) * 100. Those are algebraically identical and NUMERICALLY ARE NOT: at
# an index of exactly 0.95 the module's value is a few units in the last place BELOW the
# constant, so the `>=` test fails and a project sitting exactly on the owner's Yellow edge
# reads AMBER. It is BAC-dependent, which is the signature of the defect: at BAC 1.0 the two
# paths coincide and the same project reads Yellow.
# The 0.90 Amber edge happens to fall the other way and is correctly inclusive. A1.8 is one of
# the two CORE VOTING MODULES, so this moves a project status, not a displayed number.
# NOT REPAIRED IN THIS RUN: the repair sits inside `server/app/simulation/`, which this run is
# forbidden to modify. Reported for the owner's decision.
check("A1.8 DEFECT: CPI 0.95 does not attain the Yellow edge", vac_band(0.95)[1] >= _Y, False)
check("A1.8 DEFECT is BAC-dependent (BAC 1.0 attains it)",
      ((1.0 - 1.0 / 0.95) / 1.0) * 100 >= _Y, True)
check("A1.8 the 0.90 Amber edge IS correctly attained", vac_band(0.90)[1] >= _A, True)
# The -11.11 edge is COMPUTED from the index, not written as a rounded literal.
check("A1.8 Amber edge is (1 - 1/0.90)*100", _A, (1 - 1 / 0.90) * 100)
check("A1.8 Amber edge is NOT the literal -11.11", _A == -11.11, False)
check("A1.8 Yellow edge is (1 - 1/0.95)*100", _Y, (1 - 1 / 0.95) * 100)

print("=== A3.2 Contingency Burn: Amber INCLUDES 1.5 ===")
def burn_band(remaining, pct):
    """Exact constructions only: consumed C = (1000 - remaining)/1000, burn = C / (pct/100)."""
    r = X.run_contingency_burn({"originalContingency": 1000.0,
                                "remainingContingency": remaining,
                                "actualPctComplete": pct}, lambda: 0.5, None)
    return r.get("status_color"), r.get("normalized_burn")
# (remaining, percent complete) -> exact normalised burn
for rem, pct, burn, want in ((500.0, 50.0, 1.0, "Green"),
                             (500.0, 49.0, 1.0204081632653061, "Yellow"),
                             (750.0, 25.0,  1.0, "Green"),
                             (400.0, 50.0, 1.2, "Yellow"),
                             (250.0, 50.0, 1.5, "Amber"),
                             (200.0, 50.0, 1.6, "Red")):
    _col, _b = burn_band(rem, pct)
    check(f"burn {burn} (remaining {rem}, {pct} pct complete)", (_col, _b), (want, round(burn, 2)))
# THE BOUNDARY THE ORDER NAMES: 1.5 IS AMBER, and a hair above it is Red.
check("A3.2 exactly 1.5 is Amber (inclusive upper side)", burn_band(250.0, 50.0)[0], "Amber")
check("A3.2 just above 1.5 is Red", burn_band(249.0, 50.0)[0], "Red")
check("A3.2 exactly 1.2 is Yellow (inclusive upper side)", burn_band(400.0, 50.0)[0], "Yellow")
check("A3.2 just above 1.2 is Amber", burn_band(399.0, 50.0)[0], "Amber")

print("=== A3.5 Overhead: the banded quantity is ABSORPTION variance, not RATE variance ===")
def overhead(absorption_pct, rate_skew):
    """planned absorbed 1000; actual = 1000*(1+absorption_pct). The allocation-base drivers are
    set so the RATE variance differs from the absorption variance, proving which one bands."""
    planned_overhead = 1000.0
    actual_overhead = planned_overhead * (1 + absorption_pct)
    si = {"overheadAllocationBase": {
        "allocation_base": "direct labour hours",
        "planned_overhead": planned_overhead, "planned_driver": 100.0,
        "actual_overhead": actual_overhead, "actual_driver": 100.0 * rate_skew,
        "planned_overhead_absorbed": planned_overhead,
        "actual_overhead_incurred": actual_overhead,
        "period": "2025-01", "actual_period": "2025-01", "planned_period": "2025-01",
        "cost_code_population": "all indirect cost codes",
        "driver_source": "certified payroll", "progress_basis": "earned hours",
    }}
    return X.run_overhead_absorption(si, lambda: 0.5, None)

for pct, want in ((0.05, "Green"), (0.0501, "Yellow"), (0.10, "Yellow"),
                  (0.1001, "Amber"), (0.15, "Amber"), (0.1501, "Red"), (-0.30, "Green")):
    r = overhead(pct, 1.0)
    check(f"absorption variance {pct}", r.get("status_color"), want)
# THE DECISIVE ONE. Same absorption variance (5 per cent, Green), but the driver is halved so
# the RATE variance is 110 per cent. If the module banded the rate variance this would be Red.
_r = overhead(0.05, 0.5)
check("A3.5 rate variance is reported", round(_r.get("relative_rate_variance"), 4), 1.1)
check("A3.5 but ABSORPTION variance is what bands", _r.get("status_color"), "Green")
check("A3.5 banded quantity value", round(_r.get("absorption_variance_fraction"), 6), 0.05)

print("=== A1.6 and A1.9 DO assert bands in the running instrument (Run 107) ===")
check("A1.6 band basis is the Run 107 owner order",
      E._RUN107_BASIS_ID in E._run107_basis("section 1, A1.6", "x"), True)
check("A1.5/A1.6/A1.9 all carry the Run 107 basis id",
      E._RUN107_BASIS_ID, "owner_configured_construction_control_tolerance")

print("=== PRJ-002 period 1, from the figures the documents state ===")
BAC, EV, AC = 3000000.0, 1815000.0, 1900000.0
CPI = EV / AC
_t = E.run_tcpi({"bac": BAC, "ev": EV, "ac": AC}, lambda: 0.5, None)
_v = E.run_vac({"bac": BAC, "cpi": CPI}, lambda: 0.5, None)
check("PRJ-002 P1 CPI", round(CPI, 6), 0.955263)
check("PRJ-002 P1 TCPI raw", round(_t["tcpi"], 6), round(1185000.0 / 1100000.0, 6))
check("PRJI-002 P1 TCPI band", _t["status_color"], "Amber")
check("PRJ-002 P1 VAC pct raw", round(_v["vac_pct"], 6), round((1 - 1 / CPI) * 100, 6))
check("PRJ-002 P1 VAC band", _v["status_color"], "Yellow")
_b = X.run_contingency_burn({"originalContingency": 150000.0, "remainingContingency": 90000.0,
                             "actualPctComplete": 60.5}, lambda: 0.5, None)
check("PRJ-002 P1 contingency consumed fraction", _b.get("consumed_fraction"), 0.4)
check("PRJ-002 P1 normalised burn", _b.get("normalized_burn"), 0.66)
check("PRJ-002 P1 A3.2 band", _b.get("status_color"), "Green")

print(f"\n{ok} passed, {fail} failed")
sys.exit(1 if fail else 0)
