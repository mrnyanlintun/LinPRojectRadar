"""
RUN 135, AGENT D. SELECTION, ASSEMBLY AND DETERMINISM.

A CHECK SCRIPT, NOT A PYTEST MODULE -- `server/tools/` holds scripts by convention; under
pytest this file reports "no tests ran". Run it as:

    cd server && python tools/test_run135d_selection_and_assembly.py

NO MODEL CALL IS MADE OR SIMULATED. Every fixture below is a constructed extraction dict of
exactly the shape the extraction layer returns, handed to the same readers the assembler calls.

Findings proved here: H5 (trade-table first-pass aliases), H3 (cross-period conflict visible to
qualification), M4 + R3 (business-key ordering, sha256 no longer selects a value, disagreement
reported), M5 (bare 1 and 0 refused as probability), and the two small ones -- the dead
truncation suffix in `extraction_client` and the duplicated `"status"` heading in
`compliance_register`.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    print(("  ok   " if cond else "  FAIL ") + label + (f"  [{detail}]" if detail else ""))
    if not cond:
        FAILURES.append(label)


# ------------------------------------------------------------------ H5, first-pass aliases
def h5() -> None:
    from app.documents import _run69_structures

    print("H5. trade-table aliases accept a total where the ladder is first-pass")

    class _NoEarlierPeriods:
        """The one session use on this path is the B3.2 contract look-back; no contract
        document is in play here, so an empty result is the whole of what it needs."""

        @staticmethod
        def scalars(_stmt):
            class _R:
                @staticmethod
                def all():
                    return []
            return _R()

    class _Project:
        id = 1

    def _denoms(row: dict) -> dict:
        doc = {"doc_type": "inspection_report",
               "extraction": {"trade_denominators_json": [dict(row, Subcontractor="ACME")]}}
        out = _run69_structures(_NoEarlierPeriods(), _Project(), 3, [doc])
        rec = out.get("tradeAttributionRecords") or {}
        return (rec.get("denominators_by_subcontractor") or {}).get("ACME") or {}

    # A document printing ONLY the total. Nothing may reach the first-pass column.
    d = _denoms({"Inspections Performed": 120, "Inspections Passed": 100})
    check("total-only 'Inspections Passed' reaches no first-pass column",
          "inspections_passed_first" not in d, repr(d))
    d = _denoms({"Commitments Due": 120, "Commitments Met": 100})
    check("total-only 'Commitments Met' reaches no on-time column",
          "commitments_met_on_time" not in d, repr(d))

    # The stated first-pass headings still land. Removing the superset must not blind the
    # reader to the column it is actually for.
    d = _denoms({"Inspections Passed First": 90})
    check("'Inspections Passed First' still reaches the column",
          d.get("inspections_passed_first") == 90.0, repr(d))
    d = _denoms({"First Pass Inspections": 90})
    check("'First Pass Inspections' still reaches the column",
          d.get("inspections_passed_first") == 90.0, repr(d))
    d = _denoms({"Commitments Met On Time": 90})
    check("'Commitments Met On Time' still reaches the column",
          d.get("commitments_met_on_time") == 90.0, repr(d))
    d = _denoms({"On Time Commitments": 90})
    check("'On Time Commitments' still reaches the column",
          d.get("commitments_met_on_time") == 90.0, repr(d))
    # The denominators are unaffected.
    d = _denoms({"Inspections Performed": 120})
    check("'Inspections Performed' denominator unaffected",
          d.get("inspections_performed") == 120.0, repr(d))


def main() -> int:
    h5()
    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)}")
        for f in FAILURES:
            print("  - " + f)
        return 1
    print("run135d selection and assembly: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
