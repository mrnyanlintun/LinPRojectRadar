"""
RUN 19 -- Category 2, schedule analytics. Eleven scientific targets.

TEST AND AUDIT ONLY. This suite reads production and changes nothing. No production module
imports it.

The controlling theory is research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION
_v1.md section 11. Expected values come from run17/oracle/oracles_cat_2.py, which self proves
against the specification's worked answers at import. Production output is never the oracle.

Read run17/audit_harness.py for the two-directional proposition rule before changing anything
here: a canonical proposition that production fails must be REGISTERED with its disposition, and
a registered proposition that starts holding turns this suite red so the finding cannot fossilise.
"""

from __future__ import annotations

import datetime
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE / "run17"))
sys.path.insert(0, str(HERE / "run17" / "oracle"))

import oracles_cat_2 as O                                        # noqa: E402
from audit_harness import Audit, RESULT_HEADER, write_results    # noqa: E402
from population import population                                # noqa: E402
from app.simulation import registry as REG                       # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731

# --------------------------------------------------------------------------- the register
#
# Each key names a canonical proposition of specification section 11 that PRODUCTION DOES NOT
# SATISFY, with the Run-19 disposition it produced. Registering a proposition is not excusing
# it: every one of these is a finding carried into the remediation queue. What registration
# prevents is the suite turning red for a defect Run 19 is forbidden to fix, and equally
# prevents the defect being asserted as though it were the expected answer.
KNOWN_DEFECTS = {
    "2.4/compression-is-defined": "OWNER_DECISION_REQUIRED",
    "2.4/independent-of-spi": "OWNER_DECISION_REQUIRED",
    "2.6/banded-quantity-is-point-deviation": "CORRECT_PROXY_ONLY",
    "2.7/slip-measured-against-baseline": "METHOD_LABEL_MISMATCH",
    "2.9/time-phased": "CORRECT_PROXY_ONLY",
    "2.10/simulated-distribution": "METHOD_LABEL_MISMATCH",
    "2.11/critical-path-computed": "METHOD_LABEL_MISMATCH",
}

A = Audit("category 2", KNOWN_DEFECTS)


def run(code_id: str, si: dict) -> dict:
    return REG.run_module(code_id, si, RAND, CUTOFF)


def abstained(out: dict) -> bool:
    return bool(out.get("insufficient_data")) or out.get("status_color") is None


# =============================================================================================
# GATE -- the oracle proves itself and the population is the one the specification defines
# =============================================================================================

def gate() -> None:
    A.check("GATE", "the Category 2 oracle reproduces the specification's worked answers",
            not O.self_test(), "; ".join(O.self_test()))
    ids = {t["module_id"] for t in population()}
    for mid in ("2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8", "2.9", "2.10", "2.11"):
        A.check("GATE", f"{mid} is one of the hundred scientific targets", mid in ids)
    A.check("GATE", "2.1 and 2.10 are distinct targets and did not collide under float coercion",
            "2.1" in ids and "2.10" in ids and len({"2.1", "2.10"}) == 2)
    for code in ("A2.1", "A2.2", "A2.3", "A2.4", "A2.5", "A2.6", "A2.7", "A2.8", "A2.9",
                 "A2.10", "A2.11"):
        A.check("GATE", f"{code} is non-voting", code not in REG.CORE_VOTING_MODULES)


# =============================================================================================
# 2.1 PERT NETWORK CRITICALITY -- specification 11, "2.1"
# =============================================================================================
#
# The canonical method needs an activity network with precedence and duration distributions, and
# the specification is explicit that a hard-coded illustrative network is not project-specific
# criticality. Production removed its literal three-activity network and abstains unconditionally
# on the absent structure, which is the scientifically correct outcome rather than a failure.

def m_2_1() -> None:
    e, v = O.pert_moments(2, 4, 12)
    A.near("2.1", "known-answer: the classical PERT activity mean", e, 5.0)
    A.near("2.1", "known-answer: the classical PERT activity variance", v, (10 / 6) ** 2)
    crit = O.deterministic_critical_activities({"A": 3, "B": 2, "C": 1},
                                               [("A", "C"), ("B", "C")])
    A.check("2.1", "known-answer: the specification's network makes A and C critical and not B",
            crit == {"A", "C"}, str(sorted(crit)))

    # The canonical structure, and whether production has it.
    for label, si in (("empty input", {}),
                      ("a full EVM vector but no network",
                       {"bac": 1000, "ev": 400, "ac": 450, "pv": 500, "spi": 0.8, "cpi": 0.89,
                        "actualPctComplete": 40, "plannedPctComplete": 50}),
                      ("a schedule index alone", {"spi": 0.5})):
        out = run("A2.1", si)
        A.check("2.1", f"boundary: abstains on {label}", abstained(out),
                f"returned {out.get('status_color')!r}")

    out = run("A2.1", {"bac": 1000, "spi": 0.8})
    A.proposition(
        "2.1", "2.1/no-literal-network",
        "criticality is not reported from durations that are this file's literals rather than "
        "the project's network",
        abstained(out),
        "production returned a criticality reading with no activity network supplied")
    A.check("2.1", "missingness: the abstention says the activity network is what is missing",
            "activity network" in str(out.get("evidence_metric", "")).lower())
    A.check("2.1", "invariant: no project-level input changes the outcome while the structure "
                   "is absent, so nothing about the project can move a band that has no basis",
            all(abstained(run("A2.1", {"spi": s, "bac": b}))
                for s in (0.2, 0.8, 1.4) for b in (10, 1000, 10 ** 7)))


# =============================================================================================
# 2.2 LINE OF BALANCE -- specification 11, "2.2"
# =============================================================================================

def _lob_structure(rate_lead: float, rate_follow: float, start_lead: float = 0.0,
                   start_follow: float = 5.0, locations: int = 3) -> dict:
    packages = []
    for u in range(1, locations + 1):
        packages.append({"work_type_id": "GRADE", "location_sequence": u,
                         "production_rate_locations_per_day": rate_lead, "start_day": start_lead})
        packages.append({"work_type_id": "PAVE", "location_sequence": u,
                         "production_rate_locations_per_day": rate_follow,
                         "start_day": start_follow})
    return {"lobStructure": {"leading_work_type": "GRADE", "following_work_type": "PAVE",
                              "work_packages": packages}}


def m_2_2() -> None:
    A.near("2.2", "known-answer: the specification's planned production slope",
           O.lob_production_rate([1, 2, 3], [1, 2, 3]), 1.0)
    A.near("2.2", "known-answer: the specification's actual production slope, deteriorated",
           O.lob_production_rate([1, 2, 3], [1, 2.25, 3.5]), 0.8)
    A.check("2.2", "invariant: the actual line is slower than the planned line, which is the "
                   "direction of deterioration the specification requires be provable",
            O.lob_production_rate([1, 2, 3], [1, 2.25, 3.5])
            < O.lob_production_rate([1, 2, 3], [1, 2, 3]))

    # A following crew faster than the leading crew closes the separation; the minimum is at the
    # last location, which is the interference case the method exists to find.
    want = O.lob_separation([1, 2, 3], 0.0, 0.5, 5.0, 1.0)
    out = run("A2.2", _lob_structure(rate_lead=0.5, rate_follow=1.0))
    A.near("2.2", "known-answer: the minimum crew separation, from the two production lines",
           out.get("minimum_buffer_days"), round(want["minimum_separation_days"], 1), 0.051)
    A.check("2.2", "known-answer: the interference is located at the last location",
            out.get("critical_unit_index") == 3, str(out.get("critical_unit_index")))

    A.proposition(
        "2.2", "2.2/rates-are-measured",
        "the production rates reported are the structure's own rates, not literals of the module",
        out.get("grading_rate") == 0.5 and out.get("paving_rate") == 1.0,
        f"reported {out.get('grading_rate')!r} and {out.get('paving_rate')!r}")

    # Metamorphic: slowing the following line strictly increases the minimum separation.
    slower = run("A2.2", _lob_structure(rate_lead=0.5, rate_follow=0.4))
    A.check("2.2", "metamorphic: slowing the following line widens the minimum separation",
            slower.get("minimum_buffer_days") > out.get("minimum_buffer_days"),
            f"{slower.get('minimum_buffer_days')} vs {out.get('minimum_buffer_days')}")

    # Boundary and missingness.
    A.check("2.2", "boundary: a production rate of zero is refused, since a line of work cannot "
                   "advance at it", abstained(run("A2.2", _lob_structure(0.5, 0.0))))
    A.check("2.2", "boundary: a negative production rate is refused",
            abstained(run("A2.2", _lob_structure(0.5, -1.0))))
    A.proposition(
        "2.2", "2.2/abstains-without-repetitive-structure",
        "with no repetitive location and production-line structure the module abstains, which "
        "specification 2.2 states is the correct result",
        abstained(run("A2.2", {"spi": 0.8, "actualPctComplete": 40, "bac": 1000})))
    A.check("2.2", "missingness: the leading and following lines must both be named",
            abstained(run("A2.2", {"lobStructure": {"work_packages": [{"work_type_id": "G"}]}})))


# =============================================================================================
# 2.3 CCPM BUFFER HEALTH -- specification 11, "2.3"
# =============================================================================================

def _ccpm(original: float, remaining: float, progress: float) -> dict:
    return {"ccpmStructure": {
        "chains": [{"chain_id": "PC1", "chain_type": "PROJECT", "activity_count": 12}],
        "buffers": [{"chain_id": "PC1", "buffer_type": "PROJECT",
                     "original_buffer_days": original, "remaining_buffer_days": remaining,
                     "chain_progress_fraction": progress}]}}


def m_2_3() -> None:
    A.near("2.3", "known-answer: the specification's ten day buffer with six remaining",
           O.buffer_penetration(10, 6), 0.40)

    out = run("A2.3", _ccpm(10, 6, 0.50))
    A.near("2.3", "known-answer: production reports the same forty per cent penetration",
           out.get("pct_buffer_consumed"), 40.0, 0.051)
    A.near("2.3", "known-answer: chain completion is the chain's own progress",
           out.get("pct_chain_complete"), 50.0, 0.051)

    A.proposition(
        "2.3", "2.3/buffer-is-sized-not-inferred",
        "buffer consumption is read off a sized project buffer rather than inferred from the "
        "schedule index or percent complete, which specification 2.3 forbids",
        abstained(run("A2.3", {"spi": 0.5, "actualPctComplete": 40})))

    # Invariant: penetration is monotone in what remains, and hits its endpoints exactly.
    A.near("2.3", "invariant: an untouched buffer is nought per cent penetrated",
           run("A2.3", _ccpm(10, 10, 0.5)).get("pct_buffer_consumed"), 0.0, 1e-6)
    A.near("2.3", "invariant: a fully consumed buffer is one hundred per cent penetrated",
           run("A2.3", _ccpm(10, 0, 0.5)).get("pct_buffer_consumed"), 100.0, 1e-6)
    pens = [run("A2.3", _ccpm(10, r, 0.5)).get("pct_buffer_consumed") for r in (10, 7, 4, 1)]
    A.check("2.3", "invariant: penetration is strictly decreasing in the buffer that remains",
            all(pens[i] < pens[i + 1] for i in range(len(pens) - 1)), str(pens))

    # Boundary and invalid input.
    A.check("2.3", "boundary: a buffer sized at zero days has no share to be consumed",
            abstained(run("A2.3", _ccpm(0, 0, 0.5))))
    A.check("2.3", "invalid input: more days remaining than the buffer was sized for is refused",
            abstained(run("A2.3", _ccpm(10, 12, 0.5))))
    A.check("2.3", "invalid input: chain progress outside nought to one is refused",
            abstained(run("A2.3", _ccpm(10, 6, 1.4))))
    A.check("2.3", "missingness: a chain with no sized project buffer is refused",
            abstained(run("A2.3", {"ccpmStructure": {
                "chains": [{"chain_id": "PC1", "chain_type": "PROJECT"}], "buffers": []}})))
    A.check("2.3", "threshold: the fever chart zones move with chain completion rather than "
                   "being fixed constants, so they are a management convention and not a "
                   "mathematical property of the method",
            run("A2.3", _ccpm(10, 6, 0.20)).get("amber_threshold")
            != run("A2.3", _ccpm(10, 6, 0.60)).get("amber_threshold"))


# =============================================================================================
# 2.4 SCHEDULE COMPRESSION INDEX -- specification 11, "2.4"
# =============================================================================================
#
# The specification states plainly that there is no single universal Schedule Compression Index
# and that if the registry does not define the exact metric the disposition is
# OWNER_DECISION_REQUIRED. It also forbids Run 19 from silently substituting the example form.
# So what is testable is the declared formula's own arithmetic properties, and whether the
# quantity is anything other than a restatement of the schedule performance index.

BASE = {"baselineStart": "2026-01-01", "baselineEnd": "2026-12-31", "actualPctComplete": 40}


def m_2_4() -> None:
    out = run("A2.4", {**BASE, "spi": 0.80})
    A.near("2.4", "structure: the declared ratio is required over available duration",
           out.get("compression_ratio"), 1.25, 1e-6)

    # Scale invariance, which the declared ratio must have and which a prior floor broke.
    long_base = run("A2.4", {"baselineStart": "2026-01-01", "baselineEnd": "2026-12-31",
                             "actualPctComplete": 40, "spi": 0.50})
    short_base = run("A2.4", {"baselineStart": "2026-01-01", "baselineEnd": "2026-01-03",
                              "actualPctComplete": 40, "spi": 0.50})
    A.check("2.4", "invariant: the ratio is invariant under scaling the baseline duration",
            long_base.get("compression_ratio") == short_base.get("compression_ratio"),
            f"{long_base.get('compression_ratio')} vs {short_base.get('compression_ratio')}")
    # Monotonicity and sign.
    ratios = [run("A2.4", {**BASE, "spi": s}).get("compression_ratio")
              for s in (1.25, 1.00, 0.80, 0.50)]
    A.check("2.4", "invariant: the ratio increases as schedule performance falls",
            all(ratios[i] < ratios[i + 1] for i in range(len(ratios) - 1)), str(ratios))
    A.near("2.4", "boundary: a project exactly on plan needs no compression", ratios[1], 1.0, 1e-9)

    # Zero and negative denominators, and the not-applicable case.
    A.check("2.4", "boundary: a schedule index of zero gives no rate for remaining work and is "
                   "refused rather than raising", abstained(run("A2.4", {**BASE, "spi": 0})))
    A.check("2.4", "boundary: a negative schedule index is refused",
            abstained(run("A2.4", {**BASE, "spi": -0.5})))
    A.check("2.4", "boundary: a finished project has no remaining duration to compress and is "
                   "not applicable rather than comfortable",
            abstained(run("A2.4", {**BASE, "actualPctComplete": 100, "spi": 0.8})))
    A.check("2.4", "invalid input: a baseline finish before its start is refused",
            abstained(run("A2.4", {"baselineStart": "2026-12-31", "baselineEnd": "2026-01-01",
                                   "actualPctComplete": 40, "spi": 0.8})))
    A.check("2.4", "missingness: the baseline dates are required, not defaulted",
            abstained(run("A2.4", {"spi": 0.8, "actualPctComplete": 40})))

    # The two findings.
    A.proposition(
        "2.4", "2.4/compression-is-defined",
        "the module measures compression against a governed required completion date rather "
        "than against the rate implied by past performance",
        any(k in out for k in ("target_completion_date", "required_completion_date",
                               "compression_target")),
        "no target or required completion date is an input; the quantity is the reciprocal of "
        "the schedule performance index, and specification 2.4 leaves the exact definition to "
        "the owner rather than to this run")
    A.proposition(
        "2.4", "2.4/independent-of-spi",
        "the compression ratio carries information the schedule performance index does not",
        not all(abs(run("A2.4", {**BASE, "spi": s}).get("compression_ratio") - round(1 / s, 2))
                < 1e-9 for s in (0.5, 0.8, 1.25)),
        "the ratio is exactly one over the schedule performance index at every value tested, so "
        "it is a restatement of an existing signal and shares its lineage entirely")


# =============================================================================================
# 2.5 FLOAT CONSUMPTION RATE -- specification 11, "2.5"
# =============================================================================================

def m_2_5() -> None:
    fc = O.float_consumption_fraction(5, 2)
    A.near("2.5", "known-answer: the specification's five day baseline float, two remaining",
           fc["fraction"], 0.60)
    A.near("2.5", "known-answer: total float from the network passes, TF = LS - ES",
           O.total_float(12, 7), 5)

    out = run("A2.5", {"totalFloat": 5, "consumedFloat": 3, "actualPctComplete": 40})
    A.near("2.5", "known-answer: production reports the same sixty per cent consumed",
           out.get("consumption_rate"), 60, 0.5)

    A.check("2.5", "invariant: consumption rises monotonically with float consumed",
            [run("A2.5", {"totalFloat": 10, "consumedFloat": c,
                          "actualPctComplete": 50}).get("consumption_rate")
             for c in (0, 2, 5, 9)] == [0, 20, 50, 90])
    A.near("2.5", "boundary: no float consumed is nought per cent",
           run("A2.5", {"totalFloat": 10, "consumedFloat": 0,
                        "actualPctComplete": 50}).get("consumption_rate"), 0, 1e-9)
    A.check("2.5", "invalid input: float consumed below zero is not a quantity of float that "
                   "can have been consumed and is refused rather than handing float back",
            abstained(run("A2.5", {"totalFloat": 10, "consumedFloat": -3,
                                   "actualPctComplete": 50})))
    A.check("2.5", "boundary: no positive total float leaves no denominator",
            abstained(run("A2.5", {"totalFloat": 0, "consumedFloat": 0,
                                   "actualPctComplete": 50})))
    A.proposition(
        "2.5", "2.5/no-invented-completion",
        "float consumption is not compared against a completion figure nobody reported",
        abstained(run("A2.5", {"totalFloat": 10, "consumedFloat": 4})))
    A.proposition(
        "2.5", "2.5/float-not-fabricated-from-progress",
        "float is taken from a schedule update rather than fabricated from percent complete, "
        "which specification 2.5 forbids",
        abstained(run("A2.5", {"actualPctComplete": 40, "spi": 0.8})))
    # The banded quantity is not the canonical fraction: it is that fraction divided by
    # progress. That is a legitimate transparent normalisation, but its bands have no source.
    A.near("2.5", "structure: the banded quantity is the consumption fraction normalised by "
                  "progress, a separate derived measure from the canonical fraction",
           run("A2.5", {"totalFloat": 10, "consumedFloat": 6,
                        "actualPctComplete": 50}).get("float_stress"), 1.2, 1e-6)


# =============================================================================================
# 2.6 S-CURVE DEVIATION -- specification 11, "2.6"
# =============================================================================================

def m_2_6() -> None:
    A.near("2.6", "known-answer: the specification's planned .60 against actual .50",
           O.scurve_point_deviation(0.50, 0.60), -0.10)

    out = run("A2.6", {"actualPctComplete": 50, "plannedPctComplete": 60, "ev": 500, "pv": 600})
    A.near("2.6", "known-answer: production reports the same minus ten percentage points of "
                  "progress deviation", out.get("pct_deviation"), -10.0, 1e-6)
    A.near("2.6", "known-answer: the value deviation against planned value",
           out.get("value_deviation"), -100 * (100 / 600), 0.051)

    A.check("2.6", "invariant: a project exactly on the planned curve deviates by nothing",
            run("A2.6", {"actualPctComplete": 50, "plannedPctComplete": 50,
                         "ev": 500, "pv": 500}).get("pct_deviation") == 0)
    devs = [run("A2.6", {"actualPctComplete": a, "plannedPctComplete": 60,
                         "ev": 500, "pv": 600}).get("pct_deviation") for a in (30, 45, 60, 75)]
    A.check("2.6", "invariant: deviation increases monotonically with progress",
            all(devs[i] < devs[i + 1] for i in range(len(devs) - 1)), str(devs))

    # The out-of-domain banding the specification's guard exists to prevent.
    A.check("2.6", "invalid input: a planned progress below zero is refused rather than "
                   "inflating the deviation upward into the calm end of the band",
            abstained(run("A2.6", {"actualPctComplete": 40, "plannedPctComplete": -60,
                                   "ev": 400, "pv": 600})))
    A.check("2.6", "invalid input: progress above one hundred per cent is refused",
            abstained(run("A2.6", {"actualPctComplete": 10000, "plannedPctComplete": 50,
                                   "ev": 400, "pv": 600})))
    A.check("2.6", "invalid input: earned value below zero is refused",
            abstained(run("A2.6", {"actualPctComplete": 40, "plannedPctComplete": 50,
                                   "ev": -100, "pv": 600})))
    A.check("2.6", "boundary: planned value of zero leaves no denominator",
            abstained(run("A2.6", {"actualPctComplete": 40, "plannedPctComplete": 50,
                                   "ev": 400, "pv": 0})))
    A.check("2.6", "missingness: all four inputs are required, none defaulted",
            abstained(run("A2.6", {"actualPctComplete": 40})))

    A.proposition(
        "2.6", "2.6/banded-quantity-is-point-deviation",
        "the quantity the band reads is the specification's point deviation D(t) = Actual - "
        "Planned, rather than a composite of it with a second, differently defined deviation",
        abs((out.get("pct_deviation") + out.get("value_deviation")) / 2
            - out.get("pct_deviation")) < 1e-9,
        "the band reads the mean of the progress deviation and the earned-against-planned value "
        "deviation. Both components are transparent and correct in themselves, but their average "
        "is a composite that specification 2.6 does not define, and a single period snapshot "
        "supports only the point deviation, not longitudinal S-curve analysis")


# =============================================================================================
# 2.7 MILESTONE TREND ANALYSIS -- specification 11, "2.7"
# =============================================================================================

def _mh(*snapshots) -> dict:
    """snapshots: (period, {milestone name: forecast date}) pairs."""
    return {"milestoneHistory": [
        {"at": at, "milestones": [{"name": n, "forecast": f} for n, f in ms.items()]}
        for at, ms in snapshots]}


def m_2_7() -> None:
    slips = O.milestone_slips_against_baseline(100, [104, 108, 111])
    A.check("2.7", "known-answer: the specification's baseline day 100 with forecasts 104, 108 "
                   "and 111 gives slips of 4, 8 and 11 days", slips == [4, 8, 11], str(slips))
    A.check("2.7", "invariant: the specification's series is deteriorating, so its slip trend "
                   "has a positive slope", O.ols_slope([0, 1, 2], slips) > 0)

    out = run("A2.7", _mh(("2026-04", {"Substantial Completion": "2026-10-01"}),
                          ("2026-05", {"Substantial Completion": "2026-10-08"})))
    A.near("2.7", "known-answer: a seven day movement between two consecutive forecasts",
           out.get("mean_slip_days"), 7.0, 1e-6)
    A.check("2.7", "structure: the milestone is matched by a stable identity across periods",
            out.get("matched_count") == 1 and out.get("worst_milestone")
            == "Substantial Completion")

    A.check("2.7", "invariant: a milestone that did not move reports no movement",
            run("A2.7", _mh(("2026-04", {"M": "2026-10-01"}),
                            ("2026-05", {"M": "2026-10-01"}))).get("mean_slip_days") == 0)
    A.check("2.7", "invariant: a milestone pulled earlier reports a negative movement",
            run("A2.7", _mh(("2026-04", {"M": "2026-10-08"}),
                            ("2026-05", {"M": "2026-10-01"}))).get("mean_slip_days") == -7)
    A.check("2.7", "invariant: one badly slipping milestone is not hidden inside the average",
            run("A2.7", _mh(("2026-04", {"A": "2026-10-01", "B": "2026-10-01",
                                         "C": "2026-10-01", "D": "2026-10-01"}),
                            ("2026-05", {"A": "2026-12-01", "B": "2026-10-01",
                                         "C": "2026-10-01", "D": "2026-10-01"})))
            .get("status_color") in ("Amber", "Red"))

    A.check("2.7", "missingness: a single snapshot supports no trend claim and abstains",
            abstained(run("A2.7", _mh(("2026-04", {"M": "2026-10-01"})))))
    A.check("2.7", "missingness: no milestone history at all abstains",
            abstained(run("A2.7", {"spi": 0.8, "actualPctComplete": 40})))
    A.check("2.7", "boundary: milestones whose names do not correspond across periods are not "
                   "matched, and no movement is invented for them",
            abstained(run("A2.7", _mh(("2026-04", {"Old name": "2026-10-01"}),
                                      ("2026-05", {"New name": "2026-10-08"})))))
    A.check("2.7", "invalid input: a forecast that is not a date is not counted as a movement",
            abstained(run("A2.7", _mh(("2026-04", {"M": "not a date"}),
                                      ("2026-05", {"M": "also not a date"})))))

    # The finding. Specification 2.7 defines Slip_t as F_t minus the BASELINE B.
    three = _mh(("2026-03", {"M": "2026-10-01"}),
                ("2026-04", {"M": "2026-11-01"}),
                ("2026-05", {"M": "2026-11-01"}))
    held = run("A2.7", three)
    A.proposition(
        "2.7", "2.7/slip-measured-against-baseline",
        "slip is measured against the milestone's baseline date, as specification 2.7 defines "
        "it, rather than against the immediately preceding forecast",
        held.get("mean_slip_days") != 0,
        "a milestone that has slipped thirty-one days from its baseline and then held steady "
        "reports a mean slip of zero and bands Green. The module differences the last two "
        "forecasts, which is period-over-period forecast drift, a legitimate transparent "
        "measure but a materially different quantity from cumulative slip against baseline. No "
        "baseline milestone date is an input at all, and two snapshots cannot support the "
        "regression slope the specification names as the trend summary")


# =============================================================================================
# 2.8 LOOK-AHEAD SCHEDULE HEALTH -- specification 11, "2.8"
# =============================================================================================

def m_2_8() -> None:
    A.near("2.8", "known-answer: ten planned with three constrained is seven tenths ready",
           O.ready_fraction(10, 3), 0.70)

    out = run("A2.8", {"activitiesPlanned": 10, "activitiesConstrained": 3})
    A.near("2.8", "known-answer: production reports the complementary constraint rate of thirty "
                  "per cent, which is one minus the specification's ready fraction",
           out.get("constraint_rate"), 100 * (1 - O.ready_fraction(10, 3)), 1e-6)

    A.check("2.8", "invariant: the two orientations are complementary at every point tested",
            all(abs(run("A2.8", {"activitiesPlanned": 20,
                                 "activitiesConstrained": c}).get("constraint_rate") / 100
                    - (1 - O.ready_fraction(20, c))) < 1e-9 for c in (0, 5, 11, 20)))
    A.near("2.8", "boundary: nothing constrained is a rate of nought",
           run("A2.8", {"activitiesPlanned": 10,
                        "activitiesConstrained": 0}).get("constraint_rate"), 0, 1e-9)
    A.near("2.8", "boundary: everything constrained is a rate of one hundred",
           run("A2.8", {"activitiesPlanned": 10,
                        "activitiesConstrained": 10}).get("constraint_rate"), 100, 1e-9)
    A.proposition(
        "2.8", "2.8/no-empty-window-reads-clean",
        "a look-ahead window with nothing planned in it does not read as nothing constrained",
        abstained(run("A2.8", {"activitiesPlanned": 0, "activitiesConstrained": 0})))
    A.check("2.8", "invalid input: more constrained than planned is refused",
            abstained(run("A2.8", {"activitiesPlanned": 5, "activitiesConstrained": 9})))
    A.check("2.8", "invalid input: a negative constrained count is refused",
            abstained(run("A2.8", {"activitiesPlanned": 10, "activitiesConstrained": -2})))
    A.check("2.8", "missingness: both counts are required",
            abstained(run("A2.8", {"activitiesPlanned": 10})))
    A.check("2.8", "threshold: the module carries four bands on the constraint rate, and "
                   "specification 2.8 supplies none, so their provenance is the finding",
            run("A2.8", {"activitiesPlanned": 100,
                         "activitiesConstrained": 5}).get("status_color") == "Green"
            and run("A2.8", {"activitiesPlanned": 100,
                             "activitiesConstrained": 60}).get("status_color") == "Red")


# =============================================================================================
# 2.9 RESOURCE LOADING INDEX -- specification 11, "2.9"
# =============================================================================================

def m_2_9() -> None:
    A.near("2.9", "known-answer: demand 120 against capacity 100 loads at 1.20",
           O.load_ratio(120, 100), 1.20)
    phased = O.time_phased_load([80, 120, 100], [100, 100, 100])
    A.check("2.9", "known-answer: the time-phased vector the specification requires carries one "
                   "ratio per period", phased == [0.8, 1.2, 1.0], str(phased))

    out = run("A2.9", {"plannedLaborHours": 100, "actualLaborHours": 120})
    A.near("2.9", "known-answer: production's project-total ratio at the same two figures",
           out.get("load_ratio"), 1.20, 1e-9)
    A.check("2.9", "invariant: the ratio is scale invariant in the unit of labour hours",
            run("A2.9", {"plannedLaborHours": 1000,
                         "actualLaborHours": 1200}).get("load_ratio") == out.get("load_ratio"))
    A.check("2.9", "invariant: the ratio rises monotonically with hours actually worked",
            [run("A2.9", {"plannedLaborHours": 100,
                          "actualLaborHours": a}).get("load_ratio")
             for a in (50, 90, 110, 200)] == [0.5, 0.9, 1.1, 2.0])
    A.check("2.9", "boundary: no planned hours leaves no denominator",
            abstained(run("A2.9", {"plannedLaborHours": 0, "actualLaborHours": 10})))
    A.check("2.9", "invalid input: negative hours worked are not a quantity of work and are "
                   "refused rather than banding Red for the wrong reason",
            abstained(run("A2.9", {"plannedLaborHours": 100, "actualLaborHours": -20})))
    A.check("2.9", "missingness: both figures are required",
            abstained(run("A2.9", {"plannedLaborHours": 100})))

    A.proposition(
        "2.9", "2.9/time-phased",
        "the module models demand against available capacity per time period, as canonical "
        "resource loading is defined",
        any(k in out for k in ("load_by_period", "periods", "capacity_by_period",
                               "time_phased_load")),
        "the module compares project-total actual labour hours to project-total planned labour "
        "hours. Specification 2.9 states in terms that this is a performance proxy and not a "
        "time-phased resource loading model: planned hours are a budget, not an available "
        "capacity, and no period dimension exists on the input or the output")


# =============================================================================================
# 2.10 SCHEDULE RISK ANALYSIS P80 -- specification 11, "2.10"
# =============================================================================================

def m_2_10() -> None:
    A.near("2.10", "known-answer: Uniform(0,10) has an analytic eightieth percentile of 8",
           O.uniform_p80(0, 10), 8.0)
    # A seeded simulation of the specification's laboratory case, tolerance frozen here before
    # any result is observed: 20000 draws of a uniform, absolute tolerance 0.15 on the quantile.
    import random
    rng = random.Random(20260813)
    sample = sorted(rng.uniform(0, 10) for _ in range(20000))
    A.near("2.10", "known-answer: a seeded simulation converges to the analytic P80 within the "
                   "tolerance frozen before the run",
           O.empirical_quantile(sample, 0.80), 8.0, 0.15)
    rng2 = random.Random(20260813)
    again = sorted(rng2.uniform(0, 10) for _ in range(20000))
    A.check("2.10", "reproducibility: the same seed gives the identical sample", again == sample)

    base = {"spi": 0.80, "baselineStart": "2026-01-01", "baselineEnd": "2026-12-31",
            "actualPctComplete": 40}
    out = run("A2.10", base)
    A.check("2.10", "structure: the module reports a P50 and a P80 delay",
            out.get("p50_delay_days") is not None and out.get("p80_delay_days") is not None)
    A.check("2.10", "invariant: the P80 delay is not below the P50 delay",
            out.get("p80_delay_days") >= out.get("p50_delay_days"),
            f"{out.get('p80_delay_days')} vs {out.get('p50_delay_days')}")
    A.check("2.10", "invariant: the projected delay grows as schedule performance falls",
            [run("A2.10", {**base, "spi": s}).get("p80_delay_days")
             for s in (1.2, 1.0, 0.8, 0.5)] == sorted(
                [run("A2.10", {**base, "spi": s}).get("p80_delay_days")
                 for s in (1.2, 1.0, 0.8, 0.5)]))
    A.check("2.10", "boundary: a schedule index of zero is refused rather than raising and "
                    "losing the whole project's result to an exception",
            abstained(run("A2.10", {**base, "spi": 0})))
    A.check("2.10", "boundary: a negative schedule index is refused rather than reporting a "
                    "delay of fewer than zero days and banding Green",
            abstained(run("A2.10", {**base, "spi": -0.4})))
    A.check("2.10", "invalid input: completion outside nought to one hundred is refused",
            abstained(run("A2.10", {**base, "actualPctComplete": 140})))
    A.check("2.10", "invalid input: a baseline finish before its start is refused",
            abstained(run("A2.10", {**base, "baselineStart": "2026-12-31",
                                    "baselineEnd": "2026-01-01"})))
    A.check("2.10", "missingness: the baseline dates are required",
            abstained(run("A2.10", {"spi": 0.8, "actualPctComplete": 40})))

    A.proposition(
        "2.10", "2.10/simulated-distribution",
        "the eightieth percentile is read off an empirical simulated completion distribution "
        "produced from an activity network with duration distributions",
        any(k in out for k in ("iterations", "simulated_completions", "distribution",
                              "sample_size")),
        "no network, no duration distributions, no iterations and no sample exist. The module "
        "computes remaining duration over the schedule index for a P50 and multiplies by "
        "(1 + max(0.05, 1 - SPI) * 0.5 * 1.28) for a P80. That is a deterministic z-score "
        "uplift, which specification 2.10 states in terms is not Schedule Risk Analysis P80. "
        "The 1.28 is the normal 90th-percentile deviate, not an 80th, and the uplift is a "
        "function of the schedule index rather than of any modelled duration variance")


# =============================================================================================
# 2.11 CRITICAL PATH INDEX -- specification 11, "2.11"
# =============================================================================================

def m_2_11() -> None:
    table, finish = O.cpm_passes({"A": 3, "B": 4, "C": 2}, [("A", "C"), ("B", "C")])
    A.near("2.11", "known-answer: the specification's network finishes at day 6", finish, 6)
    A.near("2.11", "known-answer: A carries one day of total float", table["A"]["TF"], 1)
    A.near("2.11", "known-answer: B carries no total float", table["B"]["TF"], 0)
    A.near("2.11", "known-answer: C carries no total float", table["C"]["TF"], 0)
    A.check("2.11", "known-answer: B and C are critical and A is not",
            table["B"]["critical"] and table["C"]["critical"] and not table["A"]["critical"])
    # The passes are exercised on a second, independent network so the oracle is not a
    # one-example fit: a pure chain makes every activity critical.
    chain, cfin = O.cpm_passes({"X": 2, "Y": 3, "Z": 1}, [("X", "Y"), ("Y", "Z")])
    A.near("2.11", "invariant: a pure chain finishes at the sum of its durations", cfin, 6)
    A.check("2.11", "invariant: every activity on a pure chain is critical",
            all(v["critical"] for v in chain.values()))

    base = {"spi": 0.90, "plannedPctComplete": 50, "actualPctComplete": 45}
    out = run("A2.11", base)
    A.near("2.11", "structure: the declared index is the mean of progress ratio and the "
                   "schedule index", out.get("critical_path_index"), (0.9 + 0.9) / 2, 1e-9)
    A.check("2.11", "invariant: the index rises with progress against plan",
            [run("A2.11", {**base, "actualPctComplete": a}).get("critical_path_index")
             for a in (25, 40, 50, 60)] == sorted(
                [run("A2.11", {**base, "actualPctComplete": a}).get("critical_path_index")
                 for a in (25, 40, 50, 60)]))
    A.check("2.11", "boundary: no planned progress leaves the ratio no denominator and is "
                    "refused rather than averaging the schedule index with itself",
            abstained(run("A2.11", {**base, "plannedPctComplete": 0})))
    A.check("2.11", "boundary: a schedule index of zero or below is refused",
            abstained(run("A2.11", {**base, "spi": 0})))
    A.check("2.11", "invalid input: a reported progress of ten thousand per cent is refused",
            abstained(run("A2.11", {**base, "actualPctComplete": 10000})))
    A.check("2.11", "missingness: all three figures are required",
            abstained(run("A2.11", {"spi": 0.9})))

    A.proposition(
        "2.11", "2.11/critical-path-computed",
        "the module performs forward and backward passes over an activity network to establish "
        "the critical path and the total float of each activity",
        any(k in out for k in ("critical_activities", "total_float", "project_finish",
                               "path_count", "network")),
        "the index is (actual percent complete / planned percent complete + SPI) / 2. "
        "Specification 2.11 states in terms that a weighted combination of the schedule index "
        "and progress is not a critical-path calculation. No activity, no logic, no float and "
        "no path appear anywhere in the input or the output, and both terms of the mean derive "
        "from the same earned-value evidence, so the average is not two independent readings")


# =============================================================================================
# RESULT ROWS
# =============================================================================================

def _row(mid, name, basis, source, struct_req, struct_present, impl, ka, bound, miss, inv,
         stoch, repro, param, calib, thresh, cat9, lineage, disp, finding, nxt) -> dict:
    return {
        "module_id": mid, "module_name": name, "category": "2", "basis_class": basis,
        "operational_activation": "ADVISORY_ONLY", "voting_status": "non-voting",
        "primary_method_source": source,
        "canonical_structure_required": struct_req, "canonical_structure_present": struct_present,
        "implementation_verified": impl, "known_answer_pass": ka, "boundary_pass": bound,
        "missingness_pass": miss, "invariant_pass": inv, "stochastic_diagnostics_pass": stoch,
        "reproducibility_pass": repro, "parameter_provenance_status": param,
        "calibration_status": calib, "threshold_status": thresh,
        "empirical_validation_status": "NOT_DONE", "regulatory_snapshot": "n/a",
        "cat9_qualification_status": cat9, "lineage_status": lineage,
        "scientific_disposition": disp, "production_change_made": "no",
        "finding_summary": finding, "required_next_action": nxt,
        "test_names": "; ".join(A.coverage.get(mid, []))[:1800],
        "evidence_paths": ("server/tools/test_run19_category_2.py; "
                           "server/tools/run17/oracle/oracles_cat_2.py; "
                           "server/tools/run17/categories/category_2_faults.csv"),
    }


ROWS = lambda: [  # noqa: E731
    _row("2.1", "PERT Network Criticality", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 11 section 2.1; Dodin and Elmaghraby (1985) criticality indices",
         "yes", "no", "n/a", "yes", "yes", "yes", "yes", "n/a", "n/a",
         "n/a", "n/a", "n/a", "NO_RAW_INPUT_CONSUMED", "NO_EVIDENCE_EMITTED",
         "CORRECT_ABSTENTION",
         "The canonical method needs an activity network with precedence logic and three-point "
         "durations, and the corpus carries no such object. The module abstains on every input "
         "shape tested, including a complete earned-value vector, and names the activity network "
         "as what is missing. The former literal three-activity network was removed rather than "
         "gated, so no criticality index is published from stand-in durations. The oracle "
         "reproduced the specification's own network independently and confirms what the method "
         "would require. Abstention is the scientifically correct result here, not a failure.",
         "Build the activity network corpus if project-specific criticality is wanted. Until "
         "then this module correctly reports nothing."),
    _row("2.2", "Line of Balance", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 11 section 2.2; Arditi, Tokdemir and Suh (2001, 2002)",
         "yes", "conditional", "yes", "yes", "yes", "yes", "yes", "n/a", "yes",
         "n/a", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED", "RAW_UNQUALIFIED_INPUT",
         "OWN_STRUCTURE_ONLY", "THRESHOLD_CALIBRATION_BLOCKED",
         "The separation between the leading and following production lines is computed from the "
         "structure's own locations, production rates and starts, and reproduces an independent "
         "calculation of the same quantity. Crew continuity, the location sequence and the "
         "offsets are preserved, the interference case is located at the correct location, and "
         "slowing the following line widens the separation as it must. Where no repetitive "
         "structure exists the module abstains, which specification 2.2 states is correct. What "
         "has no basis is the banding: the boundaries at one and a half and three days are the "
         "module's own, and the specification supplies no universal line-of-balance threshold.",
         "Source or calibrate the minimum separation boundaries, or convert them to a declared "
         "owner policy. The measurement itself needs no change."),
    _row("2.3", "CCPM Buffer Health", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 11 section 2.3; critical chain buffer management",
         "yes", "conditional", "yes", "yes", "yes", "yes", "yes", "n/a", "yes",
         "n/a", "NOT_CALIBRATED", "OWNER_POLICY", "RAW_UNQUALIFIED_INPUT",
         "OWN_STRUCTURE_ONLY", "METHOD_PASS_CALIBRATION_PENDING",
         "Buffer penetration is consumed over original buffer, read off a sized project buffer "
         "and a real critical chain, and matches the specification's worked forty per cent "
         "exactly. It is monotone in the buffer remaining and exact at both endpoints. Inferring "
         "buffer consumption from the schedule index or percent complete is refused, which is "
         "what specification 2.3 forbids. The fever-chart zones move with chain completion "
         "rather than being fixed constants, which is the recognised fever-chart convention, but "
         "it is a management convention and not a mathematical property of the method.",
         "Record the fever-chart zone rule as a versioned owner policy so it is not read as a "
         "literature-derived constant."),
    _row("2.4", "Schedule Compression Index", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 11 section 2.4, which declines to define the metric",
         "no", "n/a", "yes", "yes", "yes", "yes", "yes", "n/a", "yes",
         "NOT_SOURCED", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED", "RAW_UNQUALIFIED_INPUT",
         "DERIVED_FROM_SPI", "OWNER_DECISION_REQUIRED",
         "The declared ratio is arithmetically sound: it is scale invariant under the baseline "
         "duration, monotone in schedule performance, exactly one at a project on plan, and it "
         "refuses a zero or negative index, a finished project and a reversed baseline. But it "
         "reduces exactly to one over the schedule performance index at every value tested, so "
         "it carries no information that signal does not already carry, and no governed required "
         "completion date is an input, so nothing is being compressed against anything. "
         "Specification 2.4 states that where the registry does not define the exact metric the "
         "disposition is an owner decision, and it forbids this run from substituting its own "
         "example form.",
         "OWNER DECISION. Define the metric: either against a governed required completion date, "
         "or retire it as a restatement of the schedule performance index."),
    _row("2.5", "Float Consumption Rate", "C. LITERATURE_SUPPORTED_ADAPTATION",
         "Specification 11 section 2.5; Al-Gahtani (2009) float allocation",
         "yes", "conditional", "yes", "yes", "yes", "yes", "yes", "n/a", "yes",
         "n/a", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED", "RAW_UNQUALIFIED_INPUT",
         "SHARED_PROGRESS_INPUT", "THRESHOLD_CALIBRATION_BLOCKED",
         "The consumption fraction is consumed over total float and matches the specification's "
         "sixty per cent exactly. Float consumed below zero is refused rather than handing float "
         "back to the project, no positive total float abstains, and float is never fabricated "
         "from percent complete. The quantity the bands actually read is not that fraction but "
         "the fraction divided by progress, a progress-normalised stress measure which is a "
         "legitimate transparent derivation but a different quantity, and its four boundaries "
         "have no source. Note honestly that total float requires a schedule network the corpus "
         "does not hold, so this module is expected to abstain in practice.",
         "Source or calibrate the stress boundaries, and name the banded quantity as the "
         "progress-normalised stress rather than the consumption rate."),
    _row("2.6", "S-Curve Deviation", "C. LITERATURE_SUPPORTED_ADAPTATION",
         "Specification 11 section 2.6; Barraza, Back and Mata (2000)",
         "yes", "partial", "yes", "yes", "yes", "yes", "yes", "n/a", "yes",
         "n/a", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED", "RAW_UNQUALIFIED_INPUT",
         "SHARED_EVM_INPUT_VECTOR", "CORRECT_PROXY_ONLY",
         "The specification's point deviation, actual cumulative less planned cumulative, is "
         "computed exactly and reproduces the worked minus ten percentage points. Its domain is "
         "properly closed: a negative planned progress no longer inflates the deviation upward "
         "into the calm end of the band, progress above one hundred per cent is refused, and a "
         "negative earned value is refused. What the band reads, however, is the mean of that "
         "point deviation and a second deviation of earned against planned value. Both parts are "
         "transparent, but the average is a composite the specification does not define, and a "
         "single snapshot supports only point deviation, not longitudinal S-curve analysis.",
         "Name the composite for what it is, or band the point deviation alone. Source the "
         "boundaries either way."),
    _row("2.7", "Milestone Trend Analysis", "C. LITERATURE_SUPPORTED_ADAPTATION",
         "Specification 11 section 2.7",
         "yes", "partial", "no", "yes", "yes", "yes", "yes", "n/a", "yes",
         "n/a", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED", "RAW_UNQUALIFIED_INPUT",
         "OWN_STRUCTURE_ONLY", "METHOD_LABEL_MISMATCH",
         "Milestones are matched by a stable identity across periods, unmatched names invent no "
         "movement, a single snapshot abstains, and one badly slipping milestone is prevented "
         "from hiding inside the average. But the movement measured is the last forecast less "
         "the PREVIOUS FORECAST, whereas specification 2.7 defines slip as the forecast less the "
         "BASELINE. A milestone that slipped thirty-one days and then held steady reports a mean "
         "slip of zero and bands Green. No baseline milestone date is an input at all, and two "
         "snapshots cannot support the regression slope the specification names as the trend "
         "summary. The implemented quantity, period-over-period forecast drift, is legitimate; "
         "the registered name means something else.",
         "P1. Carry the baseline milestone date and measure slip against it, retaining the drift "
         "measure separately if it is wanted. Require three or more snapshots for a trend claim."),
    _row("2.8", "Look-Ahead Schedule Health", "D. PCEIF_CUSTOM_TRANSPARENT_INDICATOR",
         "Specification 11 section 2.8; look-ahead and make-ready planning literature",
         "no", "n/a", "yes", "yes", "yes", "yes", "yes", "n/a", "yes",
         "n/a", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED", "RAW_UNQUALIFIED_INPUT",
         "OWN_STRUCTURE_ONLY", "THRESHOLD_CALIBRATION_BLOCKED",
         "The module measures constraint rate, which is exactly one minus the specification's "
         "ready fraction, and the complementarity holds at every point tested. It is correctly "
         "not confused with percent plan complete. A window with nothing planned in it abstains "
         "rather than reading as nothing constrained, more constrained than planned is refused, "
         "and the endpoints are exact. The four boundaries have no source and the module's own "
         "comment says so: the lean literature's percent plan complete benchmarks measure a "
         "different quantity and cannot be stretched to cover this one.",
         "Calibrate the constraint-rate boundaries or convert them to declared owner policy. "
         "Govern the look-ahead window length and the definition of constrained."),
    _row("2.9", "Resource Loading Index", "C. LITERATURE_SUPPORTED_ADAPTATION",
         "Specification 11 section 2.9",
         "yes", "no", "yes", "yes", "yes", "yes", "yes", "n/a", "yes",
         "n/a", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED", "RAW_UNQUALIFIED_INPUT",
         "SHARED_LABOUR_INPUT", "CORRECT_PROXY_ONLY",
         "The ratio implemented is arithmetically exact, scale invariant in the unit of labour "
         "hours, monotone in hours worked, refuses a zero denominator and refuses negative hours "
         "rather than banding Red for the wrong reason. But it is a project-total ratio of "
         "actual to planned labour hours, and specification 2.9 states in terms that this is a "
         "performance proxy and not a time-phased resource loading model. Planned hours are a "
         "budget, not an available capacity, and there is no period dimension anywhere in the "
         "input or the output. The proxy is honest; the canonical structure is absent.",
         "P3. Either carry time-phased demand and capacity, or rename the module for the "
         "labour-hours performance ratio it actually computes."),
    _row("2.10", "Schedule Risk Analysis P80", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 11 section 2.10; Monte Carlo schedule risk analysis",
         "yes", "no", "no", "yes", "yes", "yes", "yes", "n/a", "yes",
         "NOT_SOURCED", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED", "RAW_UNQUALIFIED_INPUT",
         "DERIVED_FROM_SPI", "METHOD_LABEL_MISMATCH",
         "The domain guards are sound: a zero index no longer raises and loses the project's "
         "whole result, a negative index no longer reports a delay below zero days and bands "
         "Green, and completion outside nought to one hundred is refused. The P80 is not below "
         "the P50 and the delay grows as performance falls. But there is no activity network, no "
         "duration distribution, no iteration count and no sample. The P80 is the P50 multiplied "
         "by one plus max(0.05, 1 minus SPI) times 0.5 times 1.28, which is a deterministic "
         "z-score uplift driven by the schedule index. Specification 2.10 states in terms that "
         "this is not Schedule Risk Analysis P80. The 1.28 is the normal ninetieth-percentile "
         "deviate, not an eightieth. An independent simulation of the specification's own "
         "Uniform(0,10) case converged to the analytic 8 within a tolerance frozen beforehand, "
         "showing what the canonical method produces and this one does not.",
         "P1. Either build the schedule simulation over a real network or rename the module for "
         "the deterministic uplift it performs. The 1.28 constant should be corrected or "
         "documented whichever route is taken."),
    _row("2.11", "Critical Path Index", "B. ESTABLISHED_CANONICAL_METHOD",
         "Specification 11 section 2.11; critical path method",
         "yes", "no", "no", "yes", "yes", "yes", "yes", "n/a", "yes",
         "n/a", "NOT_CALIBRATED", "HEURISTIC_UNCALIBRATED", "RAW_UNQUALIFIED_INPUT",
         "SHARED_EVM_INPUT_VECTOR", "METHOD_LABEL_MISMATCH",
         "An independent implementation of the forward and backward passes reproduced the "
         "specification's network exactly: finish at day six, one day of total float on A, none "
         "on B or C, B and C critical. Production performs none of that. Its index is the mean "
         "of the progress ratio and the schedule index, and specification 2.11 states in terms "
         "that a weighted combination of the schedule index and progress is not a critical-path "
         "calculation. No activity, logic, float or path appears in the input or the output. "
         "Both terms of the mean derive from the same earned-value evidence, so averaging them "
         "is not two independent readings but one reading counted twice. Its domain guards are "
         "sound and its monotonicity holds, which is why this is a labelling finding and not an "
         "arithmetic one.",
         "P1. Compute the critical path from a network, or rename the module for the composite "
         "schedule index it publishes and disclose that its two terms share one lineage."),
]


def main() -> int:
    gate()
    m_2_1(); m_2_2(); m_2_3(); m_2_4(); m_2_5(); m_2_6()
    m_2_7(); m_2_8(); m_2_9(); m_2_10(); m_2_11()
    rows = ROWS()
    write_results(HERE / "run17" / "categories" / "category_2_results.csv",
                  RESULT_HEADER, rows)
    A.check("ROWS", "eleven Category 2 result rows were written", len(rows) == 11)
    A.check("ROWS", "every row carries an allowed disposition and no production change",
            all(r["production_change_made"] == "no" for r in rows))
    return A.finish()


if __name__ == "__main__":
    sys.exit(main())
