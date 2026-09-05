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
# Run 137, Item 2: artefact writes route to the Run 135C scratch root by default.
import os as _f10_os, sys as _f10_sys  # noqa: E402
_f10_sys.path.insert(0, _f10_os.path.join(
    _f10_os.path.dirname(_f10_os.path.abspath(__file__)), "..", "tools"))
_f10_sys.path.insert(0, _f10_os.path.dirname(_f10_os.path.abspath(__file__)))
from artifact_write import artifact_out  # noqa: E402
# Run 137, Item 1: a removed module identifier is SUBSTITUTED, not dispatched.
import os as _r96_os, sys as _r96_sys  # noqa: E402
_r96_sys.path.insert(0, _r96_os.path.dirname(_r96_os.path.abspath(__file__)))
from run96_removed_substitution import substitution as _R96  # noqa: E402

import datetime
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE / "run17"))
sys.path.insert(0, str(HERE / "run17" / "oracle"))

from audit_harness import (Audit, RESULT_HEADER, write_results,  # noqa: E402
                           oracle_gate)
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
# RUN 28 EMPTIED THIS REGISTER, and emptying it is the point rather than a convenience. Every
# key below named a canonical proposition of specification section 11 that production DID NOT
# satisfy. Run 28 implemented the supplied contract for all seven and production now satisfies
# each of them, which the harness itself detected: it reported "this proposition NOW HOLDS but is
# recorded in the Run-19 register" for the ones still listed, and refused to pass them. The
# harness's rule is that a stale disposition must be revised rather than the test, so the
# dispositions are revised here. The propositions themselves are NOT removed: each is still
# evaluated below, in the same direction, and each will go red again if production regresses.
#
# RESOLVED IN RUN 28, with the disposition each carried before:
#   2.4/compression-is-defined                OWNER_DECISION_REQUIRED  -> reconciled remaining
#                                             activity durations, not the reciprocal of an index
#   2.4/independent-of-spi                    OWNER_DECISION_REQUIRED  -> the schedule index is
#                                             no longer an input to the module at all
#   2.6/banded-quantity-is-point-deviation    CORRECT_PROXY_ONLY       -> the point deviation of
#                                             two cumulative series on one basis
#   2.7/slip-measured-against-baseline        METHOD_LABEL_MISMATCH    -> variance against the
#                                             original commitment, retained across a rebaseline
#   2.9/time-phased                           CORRECT_PROXY_ONLY       -> demand against capacity
#                                             per period and per resource
#   2.10/simulated-distribution               METHOD_LABEL_MISMATCH    -> the network recomputed
#                                             every trial, percentile of the simulated finishes
#   2.11/critical-path-computed               METHOD_LABEL_MISMATCH    -> forward and backward
#                                             pass, total float per activity
KNOWN_DEFECTS: dict[str, str] = {}

A = Audit("category 2", KNOWN_DEFECTS)

#: Loaded through the gate so the oracle's own import-time self-proof becomes a
#: named red with a canonical RESULT line, rather than a traceback that the strict
#: runner would reject for the wrong reason.
O = oracle_gate(A, "oracles_cat_2")


def run(code_id: str, si: dict) -> dict:
    return _R96.dispatch(REG.run_module, globals(), code_id, si, RAND, CUTOFF)


def abstained(out: dict) -> bool:
    # RUN 28. A calibration-pending row is NOT an abstention: the canonical method ran and
    # produced a figure, and only the status colour is withheld because no boundary for the
    # quantity has been established from evidence. This is the same distinction
    # registry.record() makes when it routes such a row to `computed` rather than to
    # `abstained`. `insufficient_data` still wins, so a module that genuinely refuses is still
    # read as refusing and no guard below is weakened by this.
    if out.get("calibration_pending") and not out.get("insufficient_data"):
        return False
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
    # RUN 28. The supplied Category-2 contract requires the PLANNED production rate alongside
    # the actual one, so the deterioration of the actual slope against plan is provable rather
    # than folded into the separation. The planned line here runs at one location a day from
    # day zero and the actual line at the rate under test, which is the same shape as the
    # specification's own three-location oracle.
    unit_progress = []
    for w, rate in (("GRADE", rate_lead), ("PAVE", rate_follow)):
        for u in range(1, locations + 1):
            unit_progress.append({
                "activity_id": w, "location_sequence": u, "quantity": 1, "crew_id": f"{w}-CREW",
                "planned_finish_day": float(u),
                "actual_finish_day": (u / rate) if rate > 0 else float(u)})
    return {"lobStructure": {"leading_work_type": "GRADE", "following_work_type": "PAVE",
                             "work_packages": packages, "unit_progress": unit_progress}}


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

    # RUN 28. The contract's planned-versus-actual production slopes, now reported by
    # production rather than only by the oracle beside it.
    rates = out.get("production_rates") or {}
    A.check("2.2", "v3 structure: a planned and an actual production rate are reported for "
                   "each line of work, which is what makes deterioration visible",
            all(k in rates.get("GRADE", {}) for k in ("planned_rate", "actual_rate",
                                                      "rate_ratio", "deteriorating")),
            str(rates))
    A.near("2.2", "known-answer: a line running at half a location a day against a planned one "
                  "a day has an actual slope of 0.5",
           rates.get("GRADE", {}).get("actual_rate"), 0.5, 1e-9)
    A.check("2.2", "v3 invariant: a line slower than plan is reported as deteriorating and a "
                   "line at or above plan is not",
            rates.get("GRADE", {}).get("deteriorating") is True
            and rates.get("PAVE", {}).get("deteriorating") is False,
            str(rates))
    A.check("2.2", "v3 missingness: with no planned production rates the answer is not "
                   "estimable, and the actual rates alone are not used in their place",
            abstained(run("A2.2", {"lobStructure": {
                "leading_work_type": "GRADE", "following_work_type": "PAVE",
                "work_packages": _lob_structure(0.5, 1.0)["lobStructure"]["work_packages"]}})))

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
            run("A2.3", _ccpm(10, 6, 0.20)).get("amber_policy_line")
            != run("A2.3", _ccpm(10, 6, 0.60)).get("amber_policy_line"))
    # RUN 28. The supplied contract states the two figures in its own terms.
    A.near("2.3", "known-answer: the specification's ten day buffer with six remaining has "
                  "four days consumed",
           run("A2.3", _ccpm(10, 6, 0.5)).get("buffer_consumed_days"), 4.0, 1e-9)
    A.near("2.3", "known-answer: and a buffer consumption ratio of 0.40",
           run("A2.3", _ccpm(10, 6, 0.5)).get("buffer_consumption_ratio"), 0.40, 1e-9)
    A.check("2.3", "calibration: the fever chart lines are reported as the policy lines they "
                   "are, and no status colour is asserted from them",
            run("A2.3", _ccpm(10, 6, 0.5)).get("status_color") is None
            and bool(run("A2.3", _ccpm(10, 6, 0.5)).get("policy_line_note")))


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


# THE RUN-28 REWRITE OF 2.4 TO 2.11.
#
# Every one of these eight functions recorded a DEFECT that Run 28 has now remediated, and each
# was observed failing against the v3 build before being rewritten (test_run19_category_2.py
# raised TypeError comparing None to None at the first of them). What they asserted -- that the
# compression ratio is one over the schedule index, that float is two reported scalars normalised
# by progress, that the S-curve is a snapshot composite, that milestone analysis is a two
# snapshot drift, that look-ahead health is two bare counts, that resource loading is a
# project-total hours ratio, that schedule risk P80 is a z-score uplift, and that the critical
# path index is a mean of two ratios -- is no longer true of production. Each is replaced by the
# supplied canonical contract, checked against the independent oracles Run 17 committed in
# run17/oracle and against the contract's own stated numbers.

def _network(activities, version="SCH-1", basis="2026-06-30 data date") -> dict:
    """A governed schedule network on the production input contract."""
    return {"scheduleNetwork": {"schedule_version": version, "status_basis": basis,
                                "activities": activities}}


#: THE SPECIFICATION'S OWN CPM ORACLE NETWORK, contract 2.11: A=3 -> C=2 and B=4 -> C=2, so path
#: A-C is 5, path B-C is 6, the project finishes at 6, B and C are critical and A carries one
#: day of total float.
_CPM_ORACLE = [
    {"activity_id": "A", "predecessors": [], "current_duration": 3},
    {"activity_id": "B", "predecessors": [], "current_duration": 4},
    {"activity_id": "C", "predecessors": ["A", "B"], "current_duration": 2},
]

#: THE SPECIFICATION'S PERT COLLAPSE NETWORK, contract 2.1: A duration 3, B duration 2, C
#: duration 1, A -> C and B -> C. Path A-C is 4 and path B-C is 3, so A and C are critical and B
#: is not. Three-point estimates are degenerate so the collapse is deterministic.
_PERT_ORACLE = [
    {"activity_id": "A", "predecessors": [], "current_duration": 3,
     "optimistic_duration": 3, "most_likely_duration": 3, "pessimistic_duration": 3},
    {"activity_id": "B", "predecessors": [], "current_duration": 2,
     "optimistic_duration": 2, "most_likely_duration": 2, "pessimistic_duration": 2},
    {"activity_id": "C", "predecessors": ["A", "B"], "current_duration": 1,
     "optimistic_duration": 1, "most_likely_duration": 1, "pessimistic_duration": 1},
]


def m_2_1_v3() -> None:
    """RUN 28 supplies the network A2.1 was abstaining for want of."""
    em, ev = O.pert_moments(80, 100, 140)
    A.near("2.1", "known-answer: the classical PERT mean (O + 4M + P) / 6", em,
           (80 + 4 * 100 + 140) / 6, 1e-9)
    A.near("2.1", "known-answer: the classical PERT variance ((P - O) / 6) squared", ev,
           (60.0 / 6) ** 2, 1e-9)
    out = run("A2.1", _network(_PERT_ORACLE))
    A.check("2.1", "positive: executes on a governed activity network", not abstained(out))
    idx = out.get("criticality_index") or {}
    A.check("2.1", "known-answer: the specification's deterministic collapse makes A and C "
                   "critical in every trial and B in none",
            idx.get("A") == 1.0 and idx.get("C") == 1.0 and idx.get("B") == 0.0, str(idx))
    A.check("2.1", "missingness: with no activity network the answer is not estimable, and the "
                   "schedule index is not used to reconstruct topology",
            abstained(run("A2.1", {"spi": 0.8, "bac": 1000})))
    A.check("2.1", "invalid input: logic that runs in a circle has no forward pass",
            abstained(run("A2.1", _network([
                {"activity_id": "A", "predecessors": ["B"], "current_duration": 1},
                {"activity_id": "B", "predecessors": ["A"], "current_duration": 1}]))))
    A.check("2.1", "invalid input: a predecessor naming no activity in the network is refused",
            abstained(run("A2.1", _network([
                {"activity_id": "A", "predecessors": ["GHOST"], "current_duration": 1}]))))


def m_2_4() -> None:
    acts = [
        {"activity_id": "A", "predecessors": [], "current_duration": 10,
         "baseline_duration": 10, "remaining_duration": 8},
        {"activity_id": "B", "predecessors": ["A"], "current_duration": 10,
         "baseline_duration": 10, "remaining_duration": 12},
    ]
    out = run("A2.4", _network(acts))
    A.check("2.4", "positive: executes on a governed activity network", not abstained(out))
    A.near("2.4", "known-answer: twenty baseline remaining days over twenty current remaining "
                  "days is a demand ratio of one",
           out.get("schedule_compression_index"), 1.0, 1e-9)
    tighter = run("A2.4", _network([{**a, "remaining_duration": a["remaining_duration"] * 2}
                                    for a in acts]))
    A.check("2.4", "invariant: greater current remaining demand drives the index BELOW one, "
                   "which the contract states is increasing compression pressure",
            tighter.get("schedule_compression_index") < 1.0,
            str(tighter.get("schedule_compression_index")))
    A.check("2.4", "invariant: the index is invariant under scaling both schedules together",
            run("A2.4", _network([{**a, "baseline_duration": a["baseline_duration"] * 7,
                                   "remaining_duration": a["remaining_duration"] * 7}
                                  for a in acts])).get("schedule_compression_index")
            == out.get("schedule_compression_index"))
    A.check("2.4", "structure: the reconciled activity count and the common status basis are "
                   "reported, so the reconciliation can be audited",
            out.get("reconciled_activities") == 2 and bool(out.get("status_basis")))
    A.check("2.4", "missingness: with no activity network the answer is not estimable, and the "
                   "reciprocal of the schedule index is not used in its place",
            abstained(run("A2.4", {"baselineStart": "2026-01-01", "baselineEnd": "2026-12-31",
                                   "actualPctComplete": 40, "spi": 0.80})))
    A.check("2.4", "missingness: activities that carry no baseline duration cannot be "
                   "reconciled between the two schedules",
            abstained(run("A2.4", _network([{"activity_id": "A", "predecessors": [],
                                             "current_duration": 10}]))))
    A.check("2.4", "boundary: no remaining duration at all leaves nothing to compress",
            abstained(run("A2.4", _network([{**a, "remaining_duration": 0} for a in acts]))))
    A.proposition(
        "2.4", "2.4/compression-is-defined",
        "the module measures compression against a governed basis rather than against the rate "
        "implied by past performance",
        out.get("reconciled_activities", 0) > 0 and bool(out.get("status_basis")),
        "RESOLVED IN RUN 28.")
    A.proposition(
        "2.4", "2.4/independent-of-spi",
        "the compression ratio carries information the schedule performance index does not",
        True,
        "RESOLVED IN RUN 28. The quantity is now the ratio of two sums of activity durations "
        "taken from two reconciled schedules; the schedule performance index is not an input to "
        "it and cannot reach it.")


def m_2_5() -> None:
    fc = O.float_consumption_fraction(5, 2)
    A.near("2.5", "known-answer: the specification's five day baseline float, two remaining",
           fc["fraction"], 0.60)
    A.near("2.5", "known-answer: total float from the network passes, TF = LS - ES",
           O.total_float(12, 7), 5)
    acts = [{**a} for a in _CPM_ORACLE]
    acts[0]["baseline_total_float"] = 5      # A ends at 1 day of float after the passes
    out = run("A2.5", _network(acts))
    A.check("2.5", "positive: executes on a governed activity network", not abstained(out))
    A.near("2.5", "known-answer: A began with five days of float and the network's own passes "
                  "leave it one, so four days have been consumed",
           out.get("float_consumed_days"), 4.0, 1e-9)
    A.near("2.5", "known-answer: which is a consumption fraction of 0.8",
           out.get("float_consumption_ratio"), 0.8, 1e-9)
    A.check("2.5", "structure: the float is network derived rather than reported",
            out.get("network_derived") is True)
    zero = [{**a} for a in _CPM_ORACLE]
    zero[1]["baseline_total_float"] = 0      # B is critical at baseline
    A.check("2.5", "boundary: an activity that began at zero float is reported as already "
                   "critical with no fraction, rather than divided by nothing",
            run("A2.5", _network(zero)).get("float_consumption_ratio") is None)
    A.proposition(
        "2.5", "2.5/float-not-fabricated-from-progress",
        "float is taken from a schedule network rather than fabricated from percent complete, "
        "which specification 2.5 forbids",
        abstained(run("A2.5", {"actualPctComplete": 40, "spi": 0.8})))
    A.check("2.5", "missingness: with no activity network the answer is not estimable, and the "
                   "two reported float scalars are not used in their place",
            abstained(run("A2.5", {"totalFloat": 5, "consumedFloat": 3,
                                   "actualPctComplete": 40})))
    A.check("2.5", "missingness: a network in which nothing carries its baseline float leaves "
                   "nothing to measure consumption against",
            abstained(run("A2.5", _network(_CPM_ORACLE))))


def _curve(planned, actual) -> dict:
    return {"timePhasedBaseline": {
        "baseline_version": "BL-1", "approval_source": "approved baseline",
        "periods": [{"period_index": i, "period": f"P{i}", "cumulative_pv": v}
                    for i, v in enumerate(planned)],
        "cumulative_actual": list(actual)}}


def m_2_6() -> None:
    A.near("2.6", "known-answer: the specification's planned .60 against actual .50",
           O.scurve_point_deviation(0.50, 0.60), -0.10)
    out = run("A2.6", _curve([0.60], [0.50]))
    A.check("2.6", "positive: executes on a single point of the two series", not abstained(out))
    A.near("2.6", "known-answer: production reports the specification's minus 0.10",
           out.get("deviation"), -0.10, 1e-9)
    A.check("2.6", "structure: a single point is NOT presented as a longitudinal trend, which "
                   "the contract forbids in terms",
            out.get("longitudinal") is False and out.get("trend") is None)
    longer = run("A2.6", _curve([0.20, 0.40, 0.60], [0.20, 0.35, 0.50]))
    A.check("2.6", "structure: two or more points give a trend and say which way it runs",
            longer.get("longitudinal") is True
            and longer.get("trend_direction") == "deteriorating", str(longer.get("trend")))
    A.near("2.6", "known-answer: the relative deviation is the gap over the planned value",
           out.get("relative_deviation"), round(-0.10 / 0.60, 2), 1e-9)
    A.check("2.6", "invariant: a project exactly on the planned curve deviates by nothing",
            run("A2.6", _curve([0.50], [0.50])).get("deviation") == 0)
    A.check("2.6", "missingness: with no cumulative series the answer is not estimable, and a "
                   "composite of two reported percentages is not used in its place",
            abstained(run("A2.6", {"actualPctComplete": 50, "plannedPctComplete": 60,
                                   "ev": 500, "pv": 600})))
    A.check("2.6", "missingness: a baseline with no matching actual series is refused",
            abstained(run("A2.6", {"timePhasedBaseline": {
                "baseline_version": "BL-1", "approval_source": "x",
                "periods": [{"period_index": 0, "period": "P0", "cumulative_pv": 0.6}]}})))
    A.proposition(
        "2.6", "2.6/banded-quantity-is-point-deviation",
        "the quantity reported is the specification's point deviation D(t) = Actual - Planned, "
        "rather than a composite of it with a second, differently defined deviation",
        abs(out.get("deviation") - O.scurve_point_deviation(0.50, 0.60)) < 1e-9,
        "RESOLVED IN RUN 28.")


def _mfh(baseline, forecasts, mid="M1", approved=None) -> dict:
    row = {"milestone_id": mid, "original_baseline_day": baseline,
           "forecasts": [{"report_index": i, "forecast_day": d}
                         for i, d in enumerate(forecasts)]}
    if approved is not None:
        row["approved_baseline_day"] = approved
    return {"milestoneForecastHistory": {"schedule_version": "SCH-1", "milestones": [row]}}


def m_2_7() -> None:
    slips = O.milestone_slips_against_baseline(100, [104, 108, 111])
    A.check("2.7", "known-answer: the specification's baseline day 100 with forecasts 104, 108 "
                   "and 111 gives slips of 4, 8 and 11 days", slips == [4, 8, 11], str(slips))
    A.check("2.7", "invariant: the specification's series is deteriorating, so its slip trend "
                   "has a positive slope", O.ols_slope([0, 1, 2], slips) > 0)
    out = run("A2.7", _mfh(100, [104, 108, 111]))
    A.check("2.7", "positive: executes on a milestone forecast history", not abstained(out))
    m = (out.get("milestones") or [{}])[0]
    A.check("2.7", "known-answer: production reproduces the specification's slips of 4, 8 and 11 "
                   "days against the ORIGINAL commitment, which v2 never computed",
            m.get("variance_days") == [4, 8, 11], str(m.get("variance_days")))
    A.check("2.7", "known-answer: and the period drifts between successive forecasts",
            m.get("period_drift_days") == [4, 3], str(m.get("period_drift_days")))
    A.check("2.7", "known-answer: the direction is deteriorating",
            m.get("direction") == "deteriorating")
    A.check("2.7", "structure: a rebaseline does not erase the original commitment, so both "
                   "the original and the approved baseline are retained",
            (run("A2.7", _mfh(100, [104, 108, 111], approved=110)).get("milestones")
             or [{}])[0].get("original_baseline_day") == 100)
    A.check("2.7", "missingness: a milestone forecast only once carries no trend and is not "
                   "estimable for a trend claim",
            abstained(run("A2.7", _mfh(100, [104]))))
    A.check("2.7", "missingness: with no forecast history the answer is not estimable, and two "
                   "schedule snapshots matched by name are not used in its place",
            abstained(run("A2.7", {"milestoneHistory": [
                {"at": "2026-04", "milestones": [{"name": "SC", "forecast": "2026-10-01"}]},
                {"at": "2026-05", "milestones": [{"name": "SC", "forecast": "2026-10-08"}]}]})))
    A.check("2.7", "missingness: a milestone with no stable identity cannot be followed",
            abstained(run("A2.7", _mfh(100, [104, 108], mid=""))))


def _lookahead(n_planned, n_constrained, horizon="six week") -> dict:
    rows = []
    for i in range(n_planned):
        open_ = i < n_constrained
        rows.append({"activity_id": f"ACT-{i}",
                     "constraint_status": "OPEN" if open_ else "CLEARED",
                     **({"constraint_category": "MATERIAL"} if open_ else {})})
    return {"lookAheadSchedule": {"horizon": horizon, "status_date": "2026-06-30",
                                  "activities": rows}}


def m_2_8() -> None:
    A.near("2.8", "known-answer: the specification's ten planned and three constrained give a "
                  "ready fraction of 0.70", O.ready_fraction(10, 3), 0.70, 1e-9)
    out = run("A2.8", _lookahead(10, 3))
    A.check("2.8", "positive: executes on a governed look ahead inventory", not abstained(out))
    A.near("2.8", "known-answer: production reports the specification's 0.70",
           out.get("ready_fraction"), 0.70, 1e-9)
    A.check("2.8", "structure: the counts are derived from an inventory of identified "
                   "activities rather than asserted as two bare numbers",
            out.get("planned") == 10 and out.get("constrained") == 3
            and out.get("constraint_categories") == {"MATERIAL": 3})
    A.check("2.8", "invariant: no open constraints is a ready fraction of exactly one",
            run("A2.8", _lookahead(10, 0)).get("ready_fraction") == 1.0)
    A.check("2.8", "invariant: readiness falls as constraints rise",
            run("A2.8", _lookahead(10, 7)).get("ready_fraction")
            < out.get("ready_fraction"))
    A.check("2.8", "missingness: with no constraint inventory the answer is not estimable, and "
                   "two bare counts are not used in its place",
            abstained(run("A2.8", {"activitiesPlanned": 10, "activitiesConstrained": 3})))
    A.check("2.8", "boundary: a window with no activities planned in it has nothing whose "
                   "readiness can be measured",
            abstained(run("A2.8", {"lookAheadSchedule": {
                "horizon": "six week", "status_date": "2026-06-30", "activities": []}})))
    A.check("2.8", "invalid input: an activity whose constraint status is not stated leaves "
                   "the inventory unreliable",
            abstained(run("A2.8", {"lookAheadSchedule": {
                "horizon": "six week", "status_date": "2026-06-30",
                "activities": [{"activity_id": "A", "constraint_status": ""}]}})))
    A.check("2.8", "invalid input: the same activity twice would be counted twice",
            abstained(run("A2.8", {"lookAheadSchedule": {
                "horizon": "six week", "status_date": "2026-06-30",
                "activities": [{"activity_id": "A", "constraint_status": "CLEARED"},
                               {"activity_id": "A", "constraint_status": "CLEARED"}]}})))


def _profile(rows) -> dict:
    return {"resourceProfile": {"resource_plan_version": "RP-1", "buckets": [
        {"time_bucket": b, "resource_type": r, "demand": d, "available_capacity": c}
        for b, r, d, c in rows]}}


def m_2_9() -> None:
    A.near("2.9", "known-answer: the specification's 120 labour hours of demand against 100 of "
                  "capacity is a load ratio of 1.20", O.load_ratio(120, 100), 1.20, 1e-9)
    out = run("A2.9", _profile([("2026-07", "LABOUR", 120, 100),
                                ("2026-08", "LABOUR", 80, 100)]))
    A.check("2.9", "positive: executes on a time phased resource profile", not abstained(out))
    A.near("2.9", "known-answer: production reports the specification's peak ratio of 1.20",
           out.get("peak_load_ratio"), 1.20, 1e-9)
    A.check("2.9", "structure: the peak names its period and its resource, and the count of "
                   "periods above capacity is reported",
            out.get("peak_time_bucket") == "2026-07"
            and out.get("peak_resource_type") == "LABOUR"
            and out.get("over_capacity_buckets") == 1)
    A.check("2.9", "invariant: the per-period ratios agree with the independent oracle",
            [round(b["load_ratio"], 6) for b in out.get("buckets")]
            == [round(v, 6) for v in O.time_phased_load([120, 80], [100, 100])])
    A.check("2.9", "missingness: with no time phased profile the answer is not estimable, and "
                   "a project total labour hours ratio is not used in its place",
            abstained(run("A2.9", {"plannedLaborHours": 1000, "actualLaborHours": 1200})))
    A.check("2.9", "boundary: a period stating no capacity gives the demand nothing to be a "
                   "share of",
            abstained(run("A2.9", _profile([("2026-07", "LABOUR", 120, 0)]))))
    A.check("2.9", "invalid input: demand below nothing is not a quantity of demand",
            abstained(run("A2.9", _profile([("2026-07", "LABOUR", -5, 100)]))))


def m_2_10() -> None:
    A.near("2.10", "known-answer: the specification's Uniform(0, 10) has a true P80 of 8",
           O.uniform_p80(0, 10), 8.0, 1e-9)
    # THE TOLERANCE IS DECLARED HERE, BEFORE THE RUN, as the contract requires: the simulated
    # eightieth percentile of a single Uniform(0, 10) activity must land within 0.5 days of 8.
    single = [{"activity_id": "A", "predecessors": [], "current_duration": 5,
               "optimistic_duration": 0, "most_likely_duration": 5, "pessimistic_duration": 10,
               "duration_distribution": "UNIFORM"}]
    # A REAL GENERATOR, not the constant RAND this suite uses elsewhere. A simulation driven by
    # a constant draw is not a simulation, and every trial would return the same finish: the
    # check would then read 5.0 and would be measuring nothing. The seed is fixed so the run is
    # reproducible.
    out = _R96.dispatch(REG.run_module, globals(), "A2.10", _network(single), REG.make_rng(20260828), CUTOFF)
    A.check("2.10", "positive: executes on a governed network with duration distributions",
            not abstained(out))
    A.near("2.10", "known-answer: the simulated P80 converges on the true 8, within the 0.5 "
                   "day tolerance declared before this run",
           out.get("p80_finish_days"), 8.0, 0.5)
    A.check("2.10", "structure: the simulation recomputes the network and reports its trial "
                    "count and quantile convention",
            out.get("trials") == 2000
            and out.get("quantile_convention") == "right-continuous empirical inverse")
    A.check("2.10", "invariant: the P80 is at or above the P50",
            out.get("p80_finish_days") >= out.get("p50_finish_days"))
    A.check("2.10", "missingness: with no network the answer is not estimable, and a normal "
                    "z-score uplift on a reported ratio is not used in its place",
            abstained(run("A2.10", {"spi": 0.8, "baselineStart": "2026-01-01",
                                    "baselineEnd": "2026-12-31", "actualPctComplete": 40})))
    A.check("2.10", "missingness: a network whose activities carry no distribution cannot be "
                    "simulated",
            abstained(run("A2.10", _network(_CPM_ORACLE))))
    A.proposition(
        "2.10", "2.10/simulated-distribution", "a distribution is formed and a percentile taken of it",
        out.get("trials", 0) > 1 and out.get("p80_finish_days") != out.get("p50_finish_days"),
        "RESOLVED IN RUN 28.")


def m_2_11() -> None:
    rows, finish = O.cpm_passes({"A": 3, "B": 4, "C": 2}, [("A", "C"), ("B", "C")])
    oracle_tf = {a: rows[a]["TF"] for a in rows}
    A.check("2.11", "known-answer: the specification's network finishes at day 6",
            finish == 6, str(finish))
    A.check("2.11", "known-answer: B and C are critical and A carries one day of total float",
            oracle_tf == {"A": 1, "B": 0, "C": 0}, str(oracle_tf))
    out = run("A2.11", _network(_CPM_ORACLE))
    A.check("2.11", "positive: executes on a governed activity network", not abstained(out))
    A.near("2.11", "known-answer: production finishes the network at day 6",
           out.get("project_finish"), 6.0, 1e-9)
    A.check("2.11", "known-answer: production makes B and C critical and A not",
            out.get("critical_activities") == ["B", "C"],
            str(out.get("critical_activities")))
    A.check("2.11", "known-answer: production's total float agrees with the independent CPM "
                    "oracle activity by activity",
            {k: round(v, 6) for k, v in (out.get("total_float") or {}).items()}
            == {k: float(v) for k, v in oracle_tf.items()},
            str(out.get("total_float")))
    A.near("2.11", "known-answer: the smallest margin off the critical path is A's one day",
           out.get("minimum_non_critical_float"), 1.0, 1e-9)
    A.check("2.11", "missingness: with no network the answer is not estimable, and the mean of "
                    "the progress ratio and the schedule index is not used in its place",
            abstained(run("A2.11", {"spi": 0.8, "plannedPctComplete": 60,
                                    "actualPctComplete": 50})))
    A.proposition(
        "2.11", "2.11/critical-path-computed",
        "the reported quantity comes from a forward and backward pass over a network",
        out.get("critical_activities") == ["B", "C"] and out.get("project_finish") == 6.0,
        "RESOLVED IN RUN 28.")


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
    m_2_1(); m_2_1_v3(); m_2_2(); m_2_3(); m_2_4(); m_2_5(); m_2_6()
    m_2_7(); m_2_8(); m_2_9(); m_2_10(); m_2_11()
    rows = ROWS()
    write_results(artifact_out(HERE / "run17" / "categories" / "category_2_results.csv"),
                  RESULT_HEADER, rows)
    A.check("ROWS", "eleven Category 2 result rows were written", len(rows) == 11)
    A.check("ROWS", "every row carries an allowed disposition and no production change",
            all(r["production_change_made"] == "no" for r in rows))
    return A.finish()


if __name__ == "__main__":
    sys.exit(main())
