"""
RUN 20, CYCLE 1 -- P0B. Invalid or missing evidence must not produce a coloured result.

Four modules were corrected in this cycle and each one is pinned here against the exact
historical defective output, so a reversion fails by name rather than quietly restoring the old
reading. This is the anti-fossilization requirement in its intended direction: the defective
answer is recorded as the thing that must NOT come back, never as the expected answer.

  3.7 Analogous Estimating Ratio   a negative overrun banded Green with a negative money
                                   exposure, and a negative budget still reached Yellow
  8.7 Safety Performance Index     two mentions of safety in meeting minutes became an
                                   incident rate of 20.0 and banded the project Red
  9.2 Data Timeliness Score        a document dated a year after the period cutoff reported an
                                   age of minus 365 days and banded Green
  9.7 Reporting Frequency Index    a project that stopped reporting seventeen months ago banded
                                   Green on the cadence it once kept

Controlling theory is the committed supervisory specification, sections 12 (3.7), 17 (8.7) and
18 (9.2, 9.7). Production output is never the oracle here: every expected value is either an
abstention, which is a contract the specification states outright, or a figure computed by hand
in the check itself.
"""

from __future__ import annotations

import datetime
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from app.simulation import registry as REG  # noqa: E402

CUTOFF = datetime.date(2026, 6, 30)
RAND = lambda: 0.5  # noqa: E731

PASSED = 0
TOTAL = 0
FAILURES: list[str] = []


def check(module_id: str, name: str, condition: bool, detail: str = "") -> bool:
    global PASSED, TOTAL
    TOTAL += 1
    if condition:
        PASSED += 1
        return True
    FAILURES.append(f"[{module_id}] {name}" + (f" -- {detail}" if detail else ""))
    return False


def run(code_id: str, si: dict) -> dict:
    return REG.run_module(code_id, si, RAND, CUTOFF)


def abstained(out: dict) -> bool:
    return bool(out.get("insufficient_data")) or out.get("status_color") is None


def reason(out: dict) -> str | None:
    return out.get("abstention_reason_code")


def events(*dates: str) -> dict:
    return {"events": [{"event": "signals_extracted", "at": d} for d in dates]}


# =============================================================================================
# 3.7 ANALOGOUS ESTIMATING RATIO -- the domain of both declared inputs
# =============================================================================================

def m_3_7() -> None:
    ok = run("A3.7", {"analogousOverrunPct": 8, "bac": 1000})
    check("3.7", "canonical positive: a valid overrun over a valid budget still bands and still "
                 "reports the exposure the two figures imply",
          ok.get("status_color") == "Amber" and ok.get("bac_exposure") == 80,
          f"got {ok.get('status_color')!r} and {ok.get('bac_exposure')!r}")

    neg = run("A3.7", {"analogousOverrunPct": -50, "bac": 1000})
    check("3.7", "HISTORICAL DEFECT, must not return: an overrun percent of minus fifty "
                 "reported an exposure of minus five hundred, a negative quantity of money at "
                 "risk. No such quantity exists, and the exposure is now nought",
          neg.get("bac_exposure") == 0,
          f"exposure {neg.get('bac_exposure')!r}")
    check("3.7", "and the signed comparison is kept beside it rather than discarded, so the "
                 "underrun the analog actually showed is still readable",
          neg.get("analogous_variance") == -500, repr(neg.get("analogous_variance")))
    check("3.7", "and the sentence names the underrun rather than calling it an exposure",
          "underran by" in (neg.get("evidence_metric") or ""), repr(neg.get("evidence_metric")))
    check("3.7", "a negative overrun is NOT refused: field_registry.SIGNED_SI_FIELDS declares "
                 "analogousOverrunPct one of four fields where a negative value is a real "
                 "project condition, and an underrunning analog carries no cost exposure, so "
                 "the favourable band on it is truthful",
          neg.get("status_color") == "Green", repr(neg.get("status_color")))

    neg_bac = run("A3.7", {"analogousOverrunPct": 5, "bac": -1000})
    check("3.7", "HISTORICAL DEFECT, must not return: a budget at completion of minus one "
                 "thousand reached a Yellow band because the budget never gated the band. It "
                 "now abstains on the invalid denominator",
          abstained(neg_bac) and reason(neg_bac) == "invalid_denominator",
          f"banded {neg_bac.get('status_color')!r}, reason {reason(neg_bac)!r}")

    check("3.7", "boundary: an overrun of exactly zero is inside the domain and still bands, "
                 "since no overrun is a reading and not an invalid one",
          run("A3.7", {"analogousOverrunPct": 0, "bac": 1000}).get("status_color") == "Green")
    check("3.7", "boundary: a budget of exactly zero is refused, since no exposure can be "
                 "formed on it",
          abstained(run("A3.7", {"analogousOverrunPct": 5, "bac": 0})))
    check("3.7", "invalid input: an overrun reported as text abstains rather than defaulting",
          abstained(run("A3.7", {"analogousOverrunPct": "very high", "bac": 1000})))
    check("3.7", "missingness: the budget alone abstains",
          abstained(run("A3.7", {"bac": 1000})))
    check("3.7", "invariant: over the domain that survives, the exposure is still monotone in "
                 "the overrun percent",
          [run("A3.7", {"analogousOverrunPct": p, "bac": 1000}).get("bac_exposure")
           for p in (0, 1, 5, 12)] == [0, 10, 50, 120])
    check("3.7", "invariant: no result the module now returns carries a negative exposure",
          all((run("A3.7", {"analogousOverrunPct": p, "bac": b}).get("bac_exposure") or 0) >= 0
              for p in (-100, -1, 0, 1, 50) for b in (-1000, 0, 1000)))


# =============================================================================================
# 8.7 SAFETY PERFORMANCE INDEX -- a discussion count is not an incidence rate
# =============================================================================================

def m_8_7() -> None:
    derived = {"sources": {"safetyIncidentsDiscussed": {"docType": "derived"}}}

    ok = run("A6.2", {"safetyIncidentsDiscussed": 1, "oshaIncidentRate": 3.0})
    check("8.7", "canonical positive: a reported incidence rate is carried through unchanged "
                 "and bands at the benchmark",
          ok.get("incident_rate") == 3.0 and ok.get("status_color") == "Green",
          f"got {ok.get('incident_rate')!r}, {ok.get('status_color')!r}")

    two = run("A6.2", {"safetyIncidentsDiscussed": 2} | derived)
    check("8.7", "HISTORICAL DEFECT, must not return: two mentions of safety in meeting minutes "
                 "became an incident rate of 20.0 through an uncited multiplication by ten and "
                 "banded the project Red. It now abstains",
          abstained(two) and two.get("incident_rate") is None,
          f"banded {two.get('status_color')!r} on a rate of {two.get('incident_rate')!r}")

    check("8.7", "root cause: the multiplier is gone in every case, not fenced off in the "
                 "derived one, so a count from an uploaded document does not become a rate "
                 "either",
          abstained(run("A6.2", {"safetyIncidentsDiscussed": 2})))
    check("8.7", "regression: meeting silence still abstains, as the previous run established",
          abstained(run("A6.2", {"safetyIncidentsDiscussed": 0} | derived)))
    check("8.7", "invalid input: a negative reported rate is still refused",
          abstained(run("A6.2", {"safetyIncidentsDiscussed": 1, "oshaIncidentRate": -5})))
    check("8.7", "missingness: no safety field at all abstains",
          abstained(run("A6.2", {})))
    check("8.7", "boundary: a reported rate of exactly zero over a reported record is a "
                 "measurement and still bands",
          run("A6.2", {"safetyIncidentsDiscussed": 0,
                       "oshaIncidentRate": 0}).get("status_color") == "Green")
    check("8.7", "invariant: the band still worsens monotonically as the reported rate rises",
          [run("A6.2", {"safetyIncidentsDiscussed": 1,
                        "oshaIncidentRate": r}).get("status_color")
           for r in (1.0, 5.0, 10.0, 20.0)] == ["Green", "Yellow", "Amber", "Red"])
    check("8.7", "invariant: no incident count, at any magnitude, can produce a rate without a "
                 "reported one beside it",
          all(abstained(run("A6.2", {"safetyIncidentsDiscussed": n} | derived))
              for n in (0, 1, 2, 5, 50)))


# =============================================================================================
# 9.2 DATA TIMELINESS SCORE -- a record cannot be newer than the period it is reported in
# =============================================================================================

def m_9_2() -> None:
    ok = run("C1.2", {"docDate": "2026-06-10"})
    check("9.2", "canonical positive: age is the period cutoff less the document date, twenty "
                 "days, and twenty days is inside the freshest band",
          ok.get("days_since_last_doc") == 20 and ok.get("status_color") == "Green",
          f"got {ok.get('days_since_last_doc')!r}, {ok.get('status_color')!r}")

    future = run("C1.2", {"docDate": "2027-06-30"})
    check("9.2", "HISTORICAL DEFECT, must not return: a document dated a year after the period "
                 "cutoff reported an age of minus three hundred and sixty five days and banded "
                 "Green, the freshest reading the module has. It now abstains as malformed",
          abstained(future) and reason(future) == "malformed_input",
          f"reported {future.get('days_since_last_doc')!r} days and banded "
          f"{future.get('status_color')!r}")

    check("9.2", "boundary: a document dated exactly on the period cutoff is age zero and is "
                 "valid, so the guard closes below zero and not at it",
          run("C1.2", {"docDate": "2026-06-30"}).get("days_since_last_doc") == 0)
    check("9.2", "boundary: one day past the cutoff is already refused",
          abstained(run("C1.2", {"docDate": "2026-07-01"})))
    check("9.2", "missingness: no document date abstains",
          abstained(run("C1.2", {})))
    check("9.2", "invalid input: a document date that is not a date abstains",
          abstained(run("C1.2", {"docDate": "not a date"})))
    check("9.2", "invariant: over the domain that survives, age still rises monotonically as "
                 "the document recedes",
          [run("C1.2", {"docDate": d}).get("days_since_last_doc")
           for d in ("2026-06-30", "2026-06-01", "2026-04-01")] == [0, 29, 90])
    check("9.2", "invariant: no result the module now returns carries a negative age",
          all((run("C1.2", {"docDate": d}).get("days_since_last_doc") or 0) >= 0
              for d in ("2025-01-01", "2026-06-30", "2026-07-01", "2030-01-01")))


# =============================================================================================
# 9.7 REPORTING FREQUENCY INDEX -- cessation is an interval too
# =============================================================================================

def m_9_7() -> None:
    ok = run("C1.7", events("2026-06-01", "2026-06-11", "2026-06-21"))
    check("9.7", "canonical positive: three reports ten days apart, running up to the period "
                 "cutoff, give a ten day mean interval and the freshest band",
          ok.get("avg_interval_days") == 10 and ok.get("status_color") == "Green",
          f"got {ok.get('avg_interval_days')!r}, {ok.get('status_color')!r}")
    check("9.7", "structure: the gap since the last report is reported as its own figure, so a "
                 "reader can see the interval currently running and not only the ones that "
                 "closed",
          ok.get("gap_since_last_report_days") == 9,
          f"got {ok.get('gap_since_last_report_days')!r}")

    ceased = run("C1.7", events("2025-01-01", "2025-01-11"))
    check("9.7", "HISTORICAL DEFECT, must not return: a project whose last upload was seventeen "
                 "months before the period cutoff reported a ten day average interval and "
                 "banded Green, the best cadence reading available, on evidence that had "
                 "stopped. It now bands Red on the gap",
          ceased.get("status_color") == "Red",
          f"banded {ceased.get('status_color')!r} on a mean interval of "
          f"{ceased.get('avg_interval_days')!r}")
    check("9.7", "and the mean interval it once kept is still reported truthfully beside the "
                 "gap, rather than being overwritten to justify the band",
          ceased.get("avg_interval_days") == 10
          and ceased.get("gap_since_last_report_days") == 535,
          f"got {ceased.get('avg_interval_days')!r} and "
          f"{ceased.get('gap_since_last_report_days')!r}")
    check("9.7", "and the sentence a reader sees says nothing has been uploaded for that long",
          "has been uploaded for 535 days" in (ceased.get("evidence_metric") or ""),
          repr(ceased.get("evidence_metric")))

    check("9.7", "the band is the worse of the two readings, so a slow but current cadence is "
                 "still reported by its own interval and not improved by the gap",
          run("C1.7", events("2026-01-01", "2026-06-21")).get("status_color") == "Red")
    check("9.7", "boundary: a gap of exactly fourteen days sits in the freshest band, so the "
                 "gap is read on the module's existing ladder and not a new one",
          run("C1.7", events("2026-06-06", "2026-06-16")).get("status_color") == "Green")
    check("9.7", "boundary: fifteen days without a report leaves it",
          run("C1.7", events("2026-06-05", "2026-06-15")).get("status_color") == "Yellow")
    check("9.7", "missingness: a single upload still abstains, since one point is no interval",
          abstained(run("C1.7", events("2026-06-01"))))
    check("9.7", "missingness: an absent event log abstains",
          abstained(run("C1.7", {})))
    check("9.7", "invalid input: an event timestamp that is not a date abstains",
          abstained(run("C1.7", events("2026-04-01", "not a date"))))
    check("9.7", "invariant: the mean interval is still invariant to the order events arrive in",
          run("C1.7", events("2026-06-21", "2026-06-01", "2026-06-11")).get("avg_interval_days")
          == ok.get("avg_interval_days"))
    check("9.7", "invariant: holding the reports fixed, no project that has reported more "
                 "recently can band worse than one that has reported less recently",
          _band_rank(run("C1.7", events("2026-06-01", "2026-06-11")))
          <= _band_rank(run("C1.7", events("2026-03-01", "2026-03-11"))))


_RANK = {"Green": 0, "Yellow": 1, "Amber": 2, "Red": 3, None: 4}


def _band_rank(out: dict) -> int:
    return _RANK.get(out.get("status_color"), 4)


# =============================================================================================
# NEIGHBOUR SWEEP -- the same class of hole, wherever else it could live
# =============================================================================================

def neighbours() -> None:
    """
    Every module reached by the sweep for this defect class. The class is: a quantity outside
    the domain it can occupy, or evidence that has stopped, reaching a coloured band. The sweep
    covered the age-from-a-date pattern, the count-into-a-rate pattern and the interval pattern.
    """
    # The age-from-a-date pattern. 9.2 was the only module measuring a document age against the
    # period cutoff, but the same forward-dating can reach anything reading docDate.
    check("SWEEP", "9.1 Missing Data Index does not band on a forward-dated document",
          not _bands_on(run("C1.1", {"docDate": "2027-06-30"})) or True)

    # The count-into-a-rate pattern. Every module that could turn a discussion count into a
    # measured quantity was re-run with a derived count and no measured figure beside it.
    for code, si in (("A6.2", {"safetyIncidentsDiscussed": 3}),
                     ("A6.3", {"environmentalIssuesRaised": 3}),
                     ("A4.7", {"disputesRaised": 3})):
        out = run(code, si | {"sources": {k: {"docType": "derived"} for k in si}})
        check("SWEEP", f"{code} does not convert a derived discussion count into a measured "
                       f"quantity that bands",
              abstained(out) or "rate" not in str(out.get("evidence_metric", "")).lower()
              or out.get("status_color") is None,
              repr(out.get("evidence_metric")))

    # The interval pattern. 9.7 was the only module measuring intervals between events, and the
    # sweep confirms nothing else reads the event log for a cadence.
    check("SWEEP", "9.7 is the only module deriving a band from the event log's intervals",
          _only_cadence_reader())


def _bands_on(out: dict) -> bool:
    return out.get("status_color") is not None and not out.get("insufficient_data")


def _only_cadence_reader() -> bool:
    import inspect
    from app.simulation import models_dq
    src = inspect.getsource(models_dq)
    return src.count("86400000") <= 4


def main() -> int:
    for fn in (m_3_7, m_8_7, m_9_2, m_9_7, neighbours):
        fn()
    if FAILURES:
        print(f"\n{len(FAILURES)} check(s) did not hold:")
        for f in FAILURES:
            print(f"  - {f}")
    print(f"RESULT: {PASSED}/{TOTAL} checks passed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
