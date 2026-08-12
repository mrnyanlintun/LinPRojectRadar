"""
Run 15 Workstream A. A1.2 CUSUM: canonical known-answer, both arms, and mutation proofs.

The expected cumulative sums below were derived BY HAND from the tabular CUSUM recurrence
before production was run, and are reproduced in the Run 15 report, section 4. They are not
a copy of the production expression: they are the arithmetic of the definition

    C+_t = max(0, C+_{t-1} + (x_t - mu0) - K)      K = k*sigma
    C-_t = max(0, C-_{t-1} + (mu0 - x_t) - K)      H = h*sigma

with mu0 = 1.0, sigma = 0.10 held FIXED (passed in, not estimated), k = 0.5 and h = 5, so
K = 0.05 and H = 0.50.
"""
import os
import sys
import types

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.simulation.models_sim import cusum_series, cusum_status

PASS = 0
TOTAL = 0
FAILURES = []


def check(name, cond):
    global PASS, TOTAL
    TOTAL += 1
    if cond:
        PASS += 1
    else:
        FAILURES.append(name)


# ---- the hand-derived canonical case ------------------------------------------------
SERIES_LO = [1.02, 0.98, 1.01, 0.99, 1.00, 0.85, 0.86, 0.84, 0.87, 0.85, 0.86]
SERIES_HI = [round(2.0 - v, 10) for v in SERIES_LO]
EXPECTED_LO = [0.00, 0.00, 0.00, 0.00, 0.00, 0.10, 0.19, 0.30, 0.38, 0.48, 0.57]
EXPECTED_ZERO = [0.00] * 11
FIRST_CROSSING = 10   # 0-based; the eleventh observation is the first above H = 0.50

MU0, SIGMA, HU = 1.0, 0.10, 5


def _run(series):
    return cusum_series(series, target=MU0, sigma=SIGMA, h_units=HU)


def canonical_known_answer():
    lo = _run(SERIES_LO)
    check("K equals 0.5 sigma", abs(lo["k"] - 0.05) < 1e-12)
    check("H equals 5 sigma", abs(lo["H"] - 0.50) < 1e-12)
    check("scale is the one supplied, not re-estimated", abs(lo["sigma"] - 0.10) < 1e-12)

    # negative arm: every cumulative sum matches the hand derivation term by term
    for t, want in enumerate(EXPECTED_LO):
        check(f"C- at t{t}", abs(lo["sLo"][t] - want) < 1e-9)
    for t, want in enumerate(EXPECTED_ZERO):
        check(f"C+ stays at zero at t{t}", abs(lo["sHi"][t] - want) < 1e-9)
    check("negative arm breaches", lo["breached"] is True)
    check("first crossing is the eleventh observation", lo["breachIndex"] == FIRST_CROSSING)
    check("the breach is on the low arm", lo["sLo"][FIRST_CROSSING] > lo["H"]
          and lo["sHi"][FIRST_CROSSING] <= lo["H"])
    check("a breach reads red", cusum_status(lo) == "red")

    # positive arm: the reflected series must produce the mirror image, exactly
    hi = _run(SERIES_HI)
    for t, want in enumerate(EXPECTED_LO):
        check(f"C+ at t{t} on the reflected series", abs(hi["sHi"][t] - want) < 1e-9)
    for t in range(len(EXPECTED_ZERO)):
        check(f"C- stays at zero at t{t} on the reflected series", abs(hi["sLo"][t]) < 1e-9)
    check("positive arm breaches", hi["breached"] is True)
    check("first crossing on the positive arm is the eleventh observation",
          hi["breachIndex"] == FIRST_CROSSING)
    check("the breach is on the high arm", hi["sHi"][FIRST_CROSSING] > hi["H"])

    # a truncated series must NOT breach: the tenth observation reaches 0.48, below H
    short = _run(SERIES_LO[:10])
    check("no crossing before the cumulative sum passes H", short["breached"] is False)
    check("the last statistic below H is the hand-derived 0.48",
          abs(short["sLo"][-1] - 0.48) < 1e-9)

    # an exactly in-control series must never accumulate on either arm
    flat = _run([1.0] * 12)
    check("a series at target accumulates nothing", max(flat["stat"]) == 0.0)
    check("a series at target does not breach", flat["breached"] is False)
    check("a series at target reads green", cusum_status(flat) == "green")


# ---- mutation proofs: the ALGORITHM is corrupted, not the expectations ---------------
MUTATIONS = [
    ("drop the accumulation term",
     "hi = max(0.0, hi + (x[t] - target) - k)",
     "hi = max(0.0, (x[t] - target) - k)"),
    ("reverse the sign of the negative arm",
     "lo = max(0.0, lo + (target - x[t]) - k)",
     "lo = max(0.0, lo + (x[t] - target) - k)"),
    ("remove the reference value k from the recurrence",
     "hi = max(0.0, hi + (x[t] - target) - k)",
     "hi = max(0.0, hi + (x[t] - target))"),
    ("disable the threshold comparison",
     "if not breached and (hi > h or lo > h):",
     "if False:"),
    ("compare against the wrong threshold",
     "if not breached and (hi > h or lo > h):",
     "if not breached and (hi > 10.0 * h or lo > 10.0 * h):"),
    ("drop the reset at zero",
     "lo = max(0.0, lo + (target - x[t]) - k)",
     "lo = lo + (target - x[t]) - k"),
]


def _mutated_module(old, new):
    path = os.path.join(os.path.dirname(__file__), "..", "app", "simulation", "models_sim.py")
    src = open(path, encoding="utf-8").read()
    if old not in src:
        return None, "the mutation target is not present in the source"
    mutated = src.replace(old, new, 1)
    if mutated == src:
        return None, "the mutation did not alter a single byte"
    mod = types.ModuleType("models_sim_mutated")
    mod.__dict__["__name__"] = "app.simulation.models_sim"
    exec(compile(mutated, path, "exec"), mod.__dict__)
    return mod, None


def mutation_proofs():
    for name, old, new in MUTATIONS:
        mod, err = _mutated_module(old, new)
        check(f"mutation applies to real bytes: {name}", mod is not None and err is None)
        if mod is None:
            continue
        lo = mod.cusum_series(SERIES_LO, target=MU0, sigma=SIGMA, h_units=HU)
        hi = mod.cusum_series(SERIES_HI, target=MU0, sigma=SIGMA, h_units=HU)
        differs = (
            lo["breached"] is not True
            or lo["breachIndex"] != FIRST_CROSSING
            or any(abs(lo["sLo"][t] - EXPECTED_LO[t]) > 1e-9 for t in range(len(EXPECTED_LO)))
            or hi["breached"] is not True
            or hi["breachIndex"] != FIRST_CROSSING
            or any(abs(hi["sHi"][t] - EXPECTED_LO[t]) > 1e-9 for t in range(len(EXPECTED_LO)))
        )
        check(f"mutation breaks the canonical answer: {name}", differs)


# ---- calibration properties of the SELECTED design ----------------------------------
def selected_calibration_properties():
    """
    The selected design is the shipped one: k = 0.5 sigma, h = 5 sigma, scale estimated from
    the monitored series. These are the structural properties the calibration relies on; the
    operating characteristics themselves are in code_audit/run15_cusum_calibration.csv and
    are reproduced by tools/run15_cusum_calibration.py, which is too slow for this suite.
    """
    from app.simulation.models_sim import run_cusum
    probe = cusum_series([1.0, 1.0], target=1.0)
    check("the shipped decision interval is five scale units", probe["hUnits"] == 5)
    check("the shipped reference value is half a scale unit",
          abs(probe["k"] - 0.5 * probe["sigma"]) < 1e-12)

    # a persistent negative shift is detected; an isolated one-period spike of the same
    # depth is not. This is the designed behaviour of a CUSUM and is asserted as such.
    base = [1.0] * 12
    shifted = [1.0] * 12 + [0.85] * 12
    spike = [1.0] * 12 + [0.85] + [1.0] * 11
    noisy = [1.0 + (0.01 if i % 2 else -0.01) for i in range(24)]
    persistent = cusum_series([v + (0.012 if i % 2 else -0.012)
                               for i, v in enumerate(shifted)], target=1.0)
    isolated = cusum_series([v + (0.012 if i % 2 else -0.012)
                             for i, v in enumerate(spike)], target=1.0)
    check("a persistent level shift breaches", persistent["breached"] is True)
    check("an isolated one-period excursion of the same depth does not breach, which is "
          "the designed behaviour of a cumulative sum and not a defect",
          isolated["breached"] is False)
    check("an in-control noisy series does not breach",
          cusum_series(noisy, target=1.0)["breached"] is False)
    check("a flat in-control series does not breach",
          cusum_series(base, target=1.0)["breached"] is False)

    # the scale is estimated from the monitored series: a real change inflates it. This is
    # the shipped behaviour, measured rather than asserted away.
    jitter = lambda seq: [v + (0.012 if i % 2 else -0.012) for i, v in enumerate(seq)]
    s_clean = cusum_series(jitter([1.0] * 24), target=1.0)["sigma"]
    s_spiked = cusum_series(jitter(spike), target=1.0)["sigma"]
    check("an excursion inflates the scale that judges it", s_spiked > s_clean)

    # abstention contract is unchanged
    check("no history abstains",
          run_cusum({"spi": 1.0}, None, 1).get("insufficient_data") is True)
    check("one period abstains",
          run_cusum({"spi": 1.0, "spiHistory": [1.0]}, None, 1).get("insufficient_data") is True)
    check("no schedule index abstains",
          run_cusum({"spiHistory": [1.0, 0.9]}, None, 1).get("insufficient_data") is True)
    check("two periods compute",
          run_cusum({"spi": 0.9, "spiHistory": [1.0, 0.9]}, None, 1).get("method_class")
          == "CUSUM")


canonical_known_answer()
mutation_proofs()
selected_calibration_properties()

if FAILURES:
    for f in FAILURES:
        print("FAIL:", f)
print(f"RESULT: {PASS}/{TOTAL} checks passed")
sys.exit(0 if PASS == TOTAL else 1)
