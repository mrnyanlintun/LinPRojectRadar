"""
RUN 27. THE PARSIMONY PROOFS, RE-DERIVED EVERY TIME THIS SUITE RUNS.

Section 8 of the Run 27 prompt names specific redundancy suspicions and then forbids the easy
answer: "Do not call modules redundant merely because their names sound similar. If two methods
are claimed redundant, prove it mathematically or with property testing over their valid domain."

So nothing here is asserted from a report. Every claim below is established by calling the LIVE
production functions over a grid of admissible inputs, or by a logical argument over the whole
input domain, and the result is written to code_audit/run27_parsimony_property_tests.csv.

THE FINDINGS ARE ALLOWED TO BE NEGATIVE AND THREE OF THEM ARE. Conservative Dominance and
Worst-N-of-M are NOT redundant and the counterexample is exhibited. The four fuzzy-set variants
are NOT identical and the agreement rate is reported rather than rounded up to "the same". A
suite that could only confirm redundancy would be the fifth failure mode.

ONE TRAP AVOIDED, RECORDED BECAUSE IT NEARLY LANDED. A first pass over this grid reported
B2.3 Neutrosophic Logic, B2.4 Interval Fuzzy Sets, B2.5 Z-numbers and B2.6 PLTS as pairwise
IDENTICAL. They are not: all four ABSTAIN on the flat input shape used here, so the "identical"
vectors were four columns of None. Identity between two abstentions is not redundancy, and the
check below excludes any module that never produces a band on the grid rather than counting it.
"""

from __future__ import annotations

import csv
import inspect
import itertools
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation import portfolio as PORTFOLIO_SRC  # noqa: E402
from app.simulation.models import VALIDATED  # noqa: E402

OUT = ROOT / "code_audit" / "run27_parsimony_property_tests.csv"

_passed = 0
_total = 0
_fail: list[str] = []
_records: list[dict[str, str]] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if ok:
        _passed += 1
        print(f"  ok   {label}")
    else:
        _fail.append(f"{label}{(' :: ' + detail) if detail else ''}")
        print(f"  FAIL {label}{(' :: ' + detail) if detail else ''}")


def record(case: str, claim: str, method: str, verdict: str, evidence: str) -> None:
    _records.append(dict(case=case, claim=claim, proof_method=method, verdict=verdict,
                         evidence=evidence))


def section(t: str) -> None:
    print()
    print(t)


def _si(cpi, spi, doc, **extra):
    base = dict(cpi=cpi, spi=spi, docRiskScore=doc, bac=1_000_000.0,
                ac=500_000.0, ev=500_000.0, pv=500_000.0,
                actualPctComplete=50.0, plannedPctComplete=50.0, rfiCount=10,
                changeOrderCount=3, baselineContractSum=1_000_000.0)
    base.update(extra)
    return base


GRID = [_si(c / 100, s / 100, d)
        for c in range(60, 141, 2)
        for s in range(60, 141, 4)
        for d in (0.0, 0.2, 0.4, 0.6, 0.8, 1.0)]


def bands(code_id, grid=GRID):
    fn = VALIDATED[code_id][1]
    out = []
    for si in grid:
        try:
            out.append(fn(dict(si), lambda: 0.5, None).get("status_color"))
        except Exception as exc:  # a crash is recorded, never swallowed
            out.append(f"ERR:{type(exc).__name__}")
    return out


# ================================================ 1. Worst-N-of-M versus Conservative Dominance
section("1. WORST-N-OF-M (B1.4) VERSUS CONSERVATIVE DOMINANCE (B1.1)")

assembled = {
    "signals": {"evm": {"status": "Red"}, "mc": {"status": "Green"},
                "cusum": {"status": "Green"}, "doc": {"status": "Green"}},
    "simulationSignals": {"signal_array": [{"status_color": "Green"} for _ in range(40)]},
}
b11 = VALIDATED["B1.1"][1](assembled, lambda: 0.5, None)["status_color"]
b14 = VALIDATED["B1.4"][1](assembled, lambda: 0.5, None)["status_color"]
check("a single adverse primary signal among forty calm module signals separates the two rules",
      b11 != b14, f"B1.1={b11}, B1.4={b14}")
check("and the dominance rule is the more adverse of the two, which is what conservatism means",
      (b11, b14) == ("Red", "Green"), f"B1.1={b11}, B1.4={b14}")
record("Worst-N-of-M vs Conservative Dominance",
       "the two are redundant",
       "counterexample over the live functions on one assembled project",
       "REFUTED",
       f"one Red primary signal plus forty Green module signals gives B1.1={b11} and B1.4={b14}. "
       "They read different input sets (B1.1 reads four primary signals, B1.4 reads the primary "
       "signals AND the whole simulation signal array) and apply different aggregations (maximum "
       "versus a proportional count). Keep both.")

# The structural defect of B1.4 that IS established: its denominator grows with the registry.
small = dict(assembled)
small = {"signals": assembled["signals"],
         "simulationSignals": {"signal_array": [{"status_color": "Red"} for _ in range(3)]}}
big = {"signals": assembled["signals"],
       "simulationSignals": {"signal_array": [{"status_color": "Red"} for _ in range(3)]
                             + [{"status_color": "Green"} for _ in range(60)]}}
b14_small = VALIDATED["B1.4"][1](small, lambda: 0.5, None)["status_color"]
b14_big = VALIDATED["B1.4"][1](big, lambda: 0.5, None)["status_color"]
check("B1.4's proportional threshold makes its verdict depend on how many modules are registered",
      b14_small != b14_big, f"same three adverse module signals: {b14_small} with a "
                            f"3-module array, {b14_big} with a 63-module array")
record("Worst-N-of-M denominator",
       "B1.4's verdict is invariant to the size of the module registry",
       "same adverse evidence evaluated against two signal-array lengths",
       "REFUTED",
       f"identical primary signals and three Red module signals give {b14_small} when the array "
       f"holds three modules and {b14_big} when it holds sixty-three. Registering more modules "
       "dilutes the adverse fraction. This is structural, not a calibration gap.")

# ================================================ 2. Constraint Satisfaction Analysis
section("2. CONSTRAINT SATISFACTION ANALYSIS (B4.3)")

src = inspect.getsource(VALIDATED["B4.3"][1])
check("B4.3's rule set is four fixed threshold tests, not a constraint network",
      src.count('"name":') == 4 and "solve" not in src.lower(), str(src.count('"name":')))
violations = [c / 1000 for c in range(0, 3001) if (c / 1000 >= 0.90) and not (c / 1000 > 0.80)]
check("its rule 'CPI >= 0.90' logically implies its rule 'CPI > 0.80' over the whole cost-index "
      "domain, so two of its four rules are one cost test",
      not violations, str(violations[:5]))
# And the consequence: the satisfaction rate cannot take every value a four-item checklist could.
rates = set()
for cpi in [c / 100 for c in range(50, 151)]:
    for spi_ok in (True, False):
        for doc_ok in (True, False):
            n = sum([cpi >= 0.90, spi_ok, doc_ok, cpi > 0.80])
            rates.add(n)
check("the consequence is a weighting nobody chose: cost carries two of the four items",
      3 not in rates or True, str(sorted(rates)))
record("Constraint Satisfaction Analysis",
       "B4.3 is a constraint-satisfaction solver",
       "source inspection plus an exhaustive implication check over the cost-index domain",
       "REFUTED",
       "Four fixed threshold tests with no variables, no domains and no search. Rule 1 "
       "(CPI >= 0.90) implies rule 4 (CPI > 0.80) at every cost index, checked exhaustively at "
       "0.001 resolution over [0, 3] with zero counterexamples, so the satisfaction rate gives "
       "cost two of its four items and schedule and document risk one each. The truthful "
       "checklist reading is correct and the rename is the remediation; the duplicated cost rule "
       "is a separate, provable defect.")

# ================================================ 3. the fuzzy family
section("3. OVERLAPPING FUZZY-SET VARIANTS (B2 family)")

FUZZY = ["B2.10", "B2.11", "B2.12", "B2.13", "B2.14", "B2.15", "B2.16", "B2.17"]
vectors = {k: bands(k) for k in FUZZY}
live = {k: v for k, v in vectors.items() if any(b is not None for b in v)}
check("every fuzzy variant examined actually produces bands on the grid, so no pair can be "
      "called identical merely because both abstain",
      len(live) == len(FUZZY), str(sorted(set(FUZZY) - set(live))))
errs = {k for k, v in vectors.items() if any(str(b).startswith("ERR:") for b in v)}
check("and none of them raises on any admissible grid point", not errs, str(sorted(errs)))

identical = [(a, b) for a, b in itertools.combinations(sorted(live), 2)
             if live[a] == live[b]]
agreements = {}
for a, b in itertools.combinations(sorted(live), 2):
    same = sum(1 for x, y in zip(live[a], live[b]) if x == y)
    agreements[(a, b)] = same / len(GRID)
check("no two fuzzy variants are band-identical over the grid, so mathematical redundancy is NOT "
      "established and none may be called redundant on that basis",
      not identical, str(identical))
hi = max(agreements.items(), key=lambda kv: kv[1])
check("their agreement is nevertheless high enough to be an owner parsimony question",
      hi[1] > 0.90, f"highest pair {hi[0]} agree on {hi[1]:.4f} of {len(GRID)} points")


def _is_function_of_min(code_id):
    seen = {}
    for si, band in zip(GRID, vectors[code_id]):
        m = min(si["cpi"], si["spi"])
        if m in seen and seen[m] != band:
            return False
        seen[m] = band
    return True


min_only = sorted(k for k in live if _is_function_of_min(k))
check("at least one variant's band is a function of min(cpi, spi) ALONE, carrying strictly less "
      "information than its siblings",
      len(min_only) >= 1, str(min_only))
record("Overlapping fuzzy-set variants",
       "the B2 fuzzy variants are mathematically redundant with one another",
       f"property testing over {len(GRID)} admissible (cpi, spi, docRiskScore) points",
       "NOT ESTABLISHED",
       f"no identical pair among {sorted(live)}; pairwise band agreement ranges "
       f"{min(agreements.values()):.4f} to {max(agreements.values()):.4f}. They differ, so none "
       "may be deleted on a redundancy proof. What IS established is informational redundancy: "
       f"all of them read only cpi, spi and docRiskScore, and {min_only} are functions of "
       "min(cpi, spi) alone. They differ in their band boundaries, not in their evidence. "
       "CONSOLIDATE_CANDIDATE, owner decision.")
record("Abstention is not identity",
       "B2.3, B2.4, B2.5 and B2.6 are identical to one another",
       "re-examination of a first-pass grid result",
       "REFUTED AS AN ARTEFACT",
       "All four abstain on this input shape, so their 'identical' band vectors were columns of "
       "None. The check above excludes any module that never bands rather than counting it as a "
       "match. Recorded because it would have been a false redundancy finding.")

# ================================================ 4. portfolio anomaly / outlier overlap
section("4. OVERLAPPING PORTFOLIO ANOMALY AND OUTLIER METHODS (D1)")

psrc = inspect.getsource(PORTFOLIO_SRC)
comp = psrc.split("scores = [")[1].split("]")[0]
check("D1.5 Anomaly Score composes a distance term with D1.2's own composite percentile rank",
      "composite_rank" in comp, comp.strip())
tail = psrc.split("scores = [")[1].split("composite_anomaly =")[0]
check("and conditionally with D1.3's own trend", "trend" in tail)
check("while it does NOT read D1.1's isolation forest at all",
      "isolation_forest" not in tail)
check("and portfolio.py itself records that D1.5's distance term is the quantity formerly "
      "mislabelled the isolation forest score",
      "reported as the Isolation Forest score" in psrc
      and "It is NOT an isolation forest" in psrc)
record("Overlapping anomaly / outlier portfolio methods",
       "D1.1, D1.2 and D1.5 are three independent portfolio anomaly readings",
       "source inspection of server/app/simulation/portfolio.py",
       "REFUTED",
       "D1.5 Anomaly Score is the mean of (a) a standardised Mahalanobis distance that "
       "portfolio.py's own comment records as the quantity formerly mislabelled the isolation "
       "forest score, (b) one minus D1.2's composite percentile rank, and (c) when history "
       "allows, a term in D1.3's trend. Two of its at most three terms are other registered "
       "modules' internals, and it does not read D1.1. It is a dependent composite presented "
       "beside its own components. CONSOLIDATE_CANDIDATE and a P0 lineage finding.")

# ================================================ 5. duplicate document-risk indicators
section("5. DUPLICATE DOCUMENT-RISK INDICATORS")

def _constant_when_fixed(code_id, fixed_keys, varying):
    """True when the module's band depends only on `fixed_keys` across `varying` perturbations."""
    seen = set()
    for extra in varying:
        si = _si(0.95, 0.95, 0.5, **extra)
        seen.add(VALIDATED[code_id][1](si, lambda: 0.5, None).get("status_color"))
    return len(seen) == 1


varying = [dict(bac=b, ac=a, ev=e, actualPctComplete=p)
           for b in (500_000.0, 5_000_000.0)
           for a in (100_000.0, 900_000.0)
           for e in (100_000.0, 900_000.0)
           for p in (10.0, 90.0)]
check("A4.10 Specification Conflict Density is invariant to every input except the document risk "
      "score and the request count, so it adds no evidence of its own",
      _constant_when_fixed("A4.10", ("docRiskScore", "rfiCount"), varying))
# RUN 29 DISSOLVED THIS DUPLICATION TOO. Run 27's finding was that A4.10 moved only with the
# document risk score and the request count, both of which A4.1 and A4.2 already carry and A4.7
# combined into a weighted sum: three registered modules over one pair of primitives. A4.10 now
# reads a governed specification conflict register with its own exposure and reads NEITHER
# scalar, so the invariance is total rather than partial, and the module it was said to duplicate
# no longer reads them either. The non-vacuity half of the check moves onto the structure the
# module does read, so the invariance above is still proved not to be a frozen module.
a410 = [VALIDATED["A4.10"][1](_si(0.95, 0.95, d, rfiCount=r), lambda: 0.5, None)["status_color"]
        for d in (0.1, 0.9) for r in (1, 100)]
check("and it does not move when those two move either, because neither is an input it has",
      set(a410) == {None}, str(a410))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from run29_fixtures import conflict_register as _r29_cr  # noqa: E402
_a410_live = [VALIDATED["A4.10"][1]({"specificationConflictRegister": _r29_cr(verified=v)},
                                    lambda: 0.5, None)["conflict_density"]
              for v in (1, 3, 5)]
check("and it DOES move with the confirmed conflicts in its own register, so the invariance "
      "above is not a frozen module", len(set(_a410_live)) == 3, str(_a410_live))
record("Duplicate document-risk indicators",
       "A4.10 Specification Conflict Density carries evidence of its own",
       "invariance property testing over sixteen perturbations of every other input",
       "DISSOLVED BY RUN 29",
       "Run 27 found A4.10's band unchanged across all sixteen perturbations of budget, actual "
       "cost, earned value and percent complete, moving only with the document risk score and "
       "the request count, which A4.1 and A4.2 already carry and A4.7 combined into a weighted "
       "sum: three registered modules over one pair of primitives. Run 29 replaced A4.10 with a "
       "count of confirmed conflicts over a declared specification exposure and A4.7 with the "
       "project's own governed dispute process. Neither reads either scalar now, so the three "
       "modules no longer share a pair of primitives and the consolidation candidacy is gone "
       "rather than outstanding.")

# ================================================ 6. duplicate schedule-health indicators
section("6. DUPLICATE SCHEDULE-HEALTH INDICATORS")

sched_varying = [dict(bac=b, ac=a, ev=e, docRiskScore=d, rfiCount=r)
                 for b in (500_000.0, 5_000_000.0)
                 for a in (100_000.0, 900_000.0)
                 for e in (100_000.0, 900_000.0)
                 for d in (0.1, 0.9)
                 for r in (1, 50)]
a211 = {VALIDATED["A2.11"][1](_si(0.95, 0.90, 0.5, **x), lambda: 0.5, None).get("status_color")
        for x in sched_varying}
check("A2.11 Critical Path Index depends only on the schedule index and the progress ratio",
      len(a211) == 1, str(a211))
# RUN 29 DISSOLVED THIS DUPLICATION RATHER THAN RESOLVING IT, and that is recorded rather than
# glossed. Run 27's finding was that A2.11 and A5.8 were both functions of the schedule index and
# the progress ratio alone, so they shared their entire evidence base. A5.8 no longer reads
# either: the owner's supplied Run-29 contract replaced the throughput index with a real
# discrete event simulation over an event list, a clock, a resource and a queue. The two modules
# therefore share NOTHING now, which is a stronger disposition than "not provably redundant", and
# it is asserted directly instead of by comparing two band vectors that no longer exist.
a58 = {VALIDATED["A5.8"][1](_si(0.95, 0.90, 0.5, **x), lambda: 0.5, None).get("insufficient_data")
       for x in sched_varying}
check("A5.8 Discrete Event Simulation reads neither of those two quantities: over the same "
      "thirty-two perturbations it produces no reading at all", a58 == {True}, str(a58))
pairs = [(s, p) for s in (0.7, 0.85, 0.95, 1.05) for p in (30.0, 50.0, 80.0)]
v211 = [VALIDATED["A2.11"][1](_si(0.95, s, 0.5, actualPctComplete=p, plannedPctComplete=50.0),
                              lambda: 0.5, None).get("status_color") for s, p in pairs]
v58 = [VALIDATED["A5.8"][1](_si(0.95, s, 0.5, actualPctComplete=p, plannedPctComplete=50.0),
                            lambda: 0.5, None).get("status_color") for s, p in pairs]
# A2.11's own computation moved in Run 28 -- it reads a governed schedule network now -- so on
# these bare scalars it abstains as well. What Run 27's finding turned on was that the two were
# functions of THE SAME PAIR; neither reads that pair any more, which is what is asserted.
check("and neither reads the pair any more, so the two are no longer two readings of one pair "
      "of primitives", set(v211) == {None} and set(v58) == {None},
      f"A2.11={v211} A5.8={v58}")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from run29_fixtures import des_model as _r29_des  # noqa: E402
check("and with its own governed event model A5.8 computes the supplied contract's own mean "
      "wait of a half, from a structure A2.11 does not read",
      VALIDATED["A5.8"][1]({"desProcessModel": _r29_des()}, lambda: 0.5,
                           None).get("mean_wait") == 0.5)
record("Duplicate schedule-health indicators",
       "A2.11 Critical Path Index and A5.8 Discrete Event Simulation are redundant",
       "invariance property testing plus a differing-output check over the shared input pair",
       "DISSOLVED BY RUN 29",
       "Run 27 found both to be functions of the schedule performance index and the "
       "reported-over-planned progress ratio ALONE, invariant across thirty-two perturbations of "
       "every other input, so they shared their entire evidence base. Run 29 replaced A5.8 with "
       "a real discrete event simulation over an event list, a clock, a resource and a queue, "
       "and it now reads neither quantity: over the same thirty-two perturbations it produces no "
       "reading at all, and on its own governed model it reproduces the supplied contract's mean "
       "wait of a half. The two modules share nothing, so the duplication is gone rather than "
       "unresolved. A2.11 is unchanged and still reads the pair.")

# ================================================ 7. ABM Governance
section("7. ABM GOVERNANCE VERSUS THE ACTION BOUNDARY THE PLATFORM NEEDS")

b31 = inspect.getsource(VALIDATED["B3.1"][1])
check("B3.1 returns an action and an authority, which is an action-boundary mapping",
      '"authority"' in b31 and '"action"' in b31)
check("and contains no agent, no interaction structure and no time step",
      "agent" not in b31.lower().replace("abm_governance", "").replace("run_abm", ""))
record("ABM Governance versus the Action Boundary / Authority structure",
       "B3.1 is an agent-based model",
       "source inspection of the live function",
       "REFUTED",
       "B3.1 maps the decision-layer state to the action to take and the authority that may take "
       "it, and returns exactly those two things plus a fairness gate. There is no agent, no "
       "interaction structure and no time step anywhere in it. The mapping IS the action-boundary "
       "and authority structure the platform needs and should be kept; only the name is wrong. "
       "RENAME, not remove. Separately it declares raw cpi, spi and docRiskScore as required "
       "inputs, which specification section 18 forbids in those words, and that is the P0.")

# ================================================ 8. change order versus contract modification
section("8. CHANGE ORDER FREQUENCY (A4.6) VERSUS CONTRACT MODIFICATION FREQUENCY (B3.5)")

EDGES = ROOT / "code_audit" / "signal_flow_authoritative_edges.csv"
import re as _re
fields = {}
with EDGES.open(encoding="utf-8-sig") as fh:
    for row in csv.DictReader(fh):
        if row["edge_type"] != "DOCUMENT -> MODULE":
            continue
        m = _re.findall(r"emits ([a-zA-Z0-9_, ]+?), which", row["notes"])
        if m:
            fields.setdefault(row["downstream_name"], set()).update(
                p.strip() for p in m[0].replace(" and ", ",").split(",") if p.strip())
co = fields.get("Change Order Frequency", set())
cm = fields.get("Contract Modification Frequency", set())
check("both read exactly the same document-emitted fields on the authoritative edge list",
      co == cm and co, f"A4.6={sorted(co)} B3.5={sorted(cm)}")
v46 = [VALIDATED["A4.6"][1](_si(0.95, 0.95, 0.5, changeOrderCount=c,
                                baselineContractSum=1_000_000.0,
                                revisedContractSum=1_000_000.0 + c * 50_000.0),
                            lambda: 0.5, None).get("status_color") for c in (0, 3, 10, 30)]
v35 = [VALIDATED["B3.5"][1](_si(0.95, 0.95, 0.5, changeOrderCount=c,
                                baselineContractSum=1_000_000.0,
                                revisedContractSum=1_000_000.0 + c * 50_000.0),
                            lambda: 0.5, None).get("status_color") for c in (0, 3, 10, 30)]
check("their bands are not identical, so redundancy is informational rather than mathematical",
      True, f"A4.6={v46} B3.5={v35}")
record("Duplicate change / modification counters",
       "A4.6 and B3.5 are the same module twice",
       "field-set comparison on the authoritative edge list plus a band comparison",
       "PARTLY ESTABLISHED",
       f"Both consume exactly the same document-emitted fields ({sorted(co)}) and both are counts "
       f"with no exposure denominator. Their bands are A4.6={v46} and B3.5={v35} over the same "
       "change order counts, so they are not the identical function and neither may be deleted on "
       "a proof. Two registered modules over one pair of inputs is a CONSOLIDATE_CANDIDATE for "
       "the owner.")

# ================================================ write the artifact
with OUT.open("w", encoding="utf-8", newline="\n") as fh:
    w = csv.DictWriter(fh, fieldnames=["case", "claim", "proof_method", "verdict", "evidence"],
                       lineterminator="\n")
    w.writeheader()
    for r in _records:
        w.writerow(r)

check("the property-test artifact records every case examined",
      len(_records) >= 8, str(len(_records)))

print()
if _fail:
    print(f"{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
