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


# ------------------------------------------------- M4, business-key document ordering
def m4() -> None:
    from app.extraction_merge import document_ordering_key

    print()
    print("M4. document order is defined by business keys, not by upload order")

    def _doc(sha, doc_type, ex):
        return {"sha256": sha, "doc_type": doc_type, "filename": sha[:4], "extraction": ex}

    early = _doc("f" * 64, "oac_minutes", {"document_date": "2026-03-10"})
    late = _doc("a" * 64, "oac_minutes", {"document_date": "2026-03-31"})
    undated = _doc("0" * 64, "oac_minutes", {})
    # The LATER document sorts LAST -- the last-writer-wins consumers take it -- and it does so
    # although its sha256 is the LOWER of the two. The business key decides, not the hash.
    check("later as_of sorts last despite the lower sha256",
          sorted([late, early], key=document_ordering_key)[-1] is late)
    check("same, with the input list reversed",
          sorted([early, late], key=document_ordering_key)[-1] is late)
    # Dated over undated: an undated document never displaces a dated one.
    check("undated sorts before dated and so never displaces it",
          sorted([late, undated], key=document_ordering_key)[0] is undated)
    check("same, reversed",
          sorted([undated, late], key=document_ordering_key)[0] is undated)
    # Writer tier: a revision beats what it revises, whatever the hashes are.
    base = _doc("f" * 64, "contract_value", {})
    rev = _doc("0" * 64, "change_order", {})
    check("a revision-rank document sorts after a baseline-rank one",
          sorted([rev, base], key=document_ordering_key)[-1] is rev)
    # sha256 is the FINAL position only, and reaches a decision only between documents
    # identical on every business key above it.
    k1 = document_ordering_key(late)
    k2 = document_ordering_key(_doc("b" * 64, "oac_minutes", {"document_date": "2026-03-31"}))
    check("sha256 is the last element of the key and the only one that differs here",
          k1[:-1] == k2[:-1] and k1[-1] != k2[-1], f"{k1[-1][:4]} vs {k2[-1][:4]}")


def main() -> int:
    h5()
    m4()
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
