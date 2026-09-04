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


# ------------------------------- H3 + R3, qualification sees what selection sees
def h3_r3() -> None:
    from app.documents import _evidence_qualification
    from app.extraction_merge import (
        _perm_pick, _snap_pick, emit_observations, select_signal_inputs,
        unresolved_value_conflicts,
    )
    from app.field_registry import IDENTITY_FIELDS

    print()
    print("H3 + R3. a cross-period conflict is visible to qualification, and sha256 no longer "
          "settles a disagreement in silence")

    # The owner's stated proof. Two cost reports in DIFFERENT periods, the SAME date, the SAME
    # writer tier 0, `original_contingency` 500,000 against 300,000. The higher sha256 wins the
    # selection; before Run 135 `material_conflicts` was EMPTY.
    early = {"sha256": "a" * 64, "doc_type": "cost_report", "filename": "p1.pdf",
             "extraction": {"report_date": "2026-03-31", "original_contingency": 500000}}
    late = {"sha256": "f" * 64, "doc_type": "cost_report", "filename": "p2.pdf",
            "extraction": {"report_date": "2026-03-31", "original_contingency": 300000}}
    own = emit_observations(late)
    carried = [o for o in emit_observations(early)
               if str(o.get("field")) in IDENTITY_FIELDS]

    si = select_signal_inputs(own, None, carried=carried)
    eq = _evidence_qualification(2, own, carried=carried)
    named = [c["field"] for c in eq["material_conflicts"]]
    check("the cross-period disagreement is named in material_conflicts",
          "originalContingency" in named, f"selected {si['originalContingency']}, conflicts {named}")
    # The period's own view of "as of when does this period speak" must NOT widen with it.
    check("effective_date is still derived from the period's own observations only",
          eq["effective_date"] == "2026-03-31", str(eq["effective_date"]))
    # A period with no carried set is unchanged, and an agreeing carried set raises nothing.
    agree = [dict(o) for o in carried]
    for o in agree:
        if o.get("field") == "originalContingency":
            o["value"] = 300000
    eq_ok = _evidence_qualification(2, own, carried=agree)
    check("carried evidence that AGREES reports no conflict",
          not [c for c in eq_ok["material_conflicts"]
               if c["field"] == "originalContingency"],
          str([c["field"] for c in eq_ok["material_conflicts"]]))

    # R3 directly. Two observations identical on every business key, differing only in value.
    def _obs(field, value, sha, kind_tier=0, as_of=None, doc_type="cost_report"):
        from datetime import date as _d
        return {"field": field, "value": value, "sha256": sha, "tier": kind_tier,
                "as_of": as_of or _d(2026, 3, 31), "rank": 1, "doc_type": doc_type,
                "kind": None, "entity_key": "", "entity_state": None}

    pair = [_obs("bac", 10_000_000, "1" * 64), _obs("bac", 12_000_000, "9" * 64)]
    rep = unresolved_value_conflicts(pair)
    check("keys exhausted and values disagree is REPORTED", [c["field"] for c in rep] == ["bac"],
          str(rep and rep[0]["distinct_values"]))
    same = [_obs("bac", 10_000_000, "1" * 64), _obs("bac", 10_000_000, "9" * 64)]
    check("keys exhausted and values AGREE is not reported (R3 permits the hash here)",
          unresolved_value_conflicts(same) == [], str(unresolved_value_conflicts(same)))
    # Selection still returns a value rather than blanking the field.
    check("selection still returns a figure on a reported disagreement",
          _snap_pick(pair)["value"] in (10_000_000, 12_000_000))
    # Order independence of the pick is retained -- the point of R3 is not that the pick moved.
    check("the pick is the same in either argument order",
          _snap_pick(pair)["value"] == _snap_pick(list(reversed(pair)))["value"])
    check("the same holds for the PERMANENT pick",
          _perm_pick(pair)["value"] == _perm_pick(list(reversed(pair)))["value"])
    # A field decided by a BUSINESS key is not reported: the keys were not exhausted.
    from datetime import date as _date
    decided = [_obs("bac", 10_000_000, "9" * 64, as_of=_date(2026, 1, 1)),
               _obs("bac", 12_000_000, "1" * 64, as_of=_date(2026, 3, 31))]
    check("a disagreement the business keys DO settle is not reported as unresolved",
          unresolved_value_conflicts(decided) == [], str(unresolved_value_conflicts(decided)))


# --------------------------------- H4, the archive filter reaches every store and reader
#
# THE ONLY DB-BACKED CHECK IN THIS FILE. It needs a migrated schema, so it is SKIPPED rather
# than failed where `DATABASE_URL` is unset; the count is reported either way and a skip is
# never counted as a pass. Point it at a throwaway SQLite file and run `alembic upgrade head`
# first:
#     DATABASE_URL=sqlite:///./run135d.db python -m alembic upgrade head
#     DATABASE_URL=sqlite:///./run135d.db python tools/test_run135d_selection_and_assembly.py
def h4() -> None:
    import os
    import uuid
    from datetime import datetime, timezone

    print()
    print("H4. the archive filter reaches every projection store and reader")
    if not os.environ.get("DATABASE_URL"):
        print("  SKIP  DATABASE_URL is unset; this check needs a migrated throwaway database")
        return

    from app.db import build_engine, build_session_factory
    from app.documents import (
        _milestone_history, _period_documents, _persist_schedule_activities,
        _schedule_display, _schedule_snapshot,
    )
    from app.models import Project
    from app.research_models import Document, DocumentUpload
    from app.settings import load_settings

    session = build_session_factory(build_engine(load_settings()))()
    milestones = [
        {"Activity ID": "D100", "Description": "Foundations",
         "Baseline Start": "2026-01-05", "Baseline Finish": "2026-02-20",
         "Current Finish": "2026-04-30", "Percent Complete": 40},
        {"Activity ID": "D200", "Description": "Steel",
         "Baseline Start": "2026-02-01", "Baseline Finish": "2026-03-15",
         "Current Finish": "2026-05-30", "Percent Complete": 10},
    ]

    def _one(archived: bool):
        project = Project(id=uuid.uuid4(), legacy_id=f"PRJ-135D-{uuid.uuid4().hex[:10]}",
                          doc={})
        session.add(project)
        session.flush()
        doc = Document(sha256=uuid.uuid4().hex * 2, filename="schedule.xlsx",
                       doc_type="schedule_update",
                       extraction={"data_date": "2026-03-31",
                                   "milestones_json": milestones})
        session.add(doc)
        session.flush()
        up = DocumentUpload(project_id=project.id, period=1, document_id=doc.document_id,
                            uploaded_by="run135d", uploaded_at=datetime.now(timezone.utc))
        if archived:
            up.archived_at = datetime.now(timezone.utc)
        session.add(up)
        session.flush()
        inserted = _persist_schedule_activities(session, project, 1)
        session.flush()
        return {
            "period_documents": len(_period_documents(session, project, 1)),
            "inserted": inserted,
            "snapshot": _schedule_snapshot(session, project, 1),
            "display": _schedule_display(session, project, 1),
            "history": len(_milestone_history(session, project, 1)),
        }

    try:
        arch = _one(archived=True)
        check("_period_documents sees nothing of the archived document",
              arch["period_documents"] == 0, str(arch["period_documents"]))
        check("_persist_schedule_activities stores nothing from it",
              arch["inserted"] == 0, str(arch["inserted"]))
        check("_schedule_snapshot returns nothing from it",
              arch["snapshot"] is None, str(arch["snapshot"]))
        check("_schedule_display returns nothing from it",
              arch["display"] is None, str(arch["display"]))
        check("milestoneHistory -- A2.7's input -- carries no snapshot from it",
              arch["history"] == 0, str(arch["history"]))
        # The filter must not over-block: an ordinary live document is untouched.
        live = _one(archived=False)
        check("a LIVE document still reaches all five",
              (live["period_documents"], live["inserted"], live["history"]) == (1, 2, 1)
              and live["snapshot"] is not None and live["display"] is not None,
              str((live["period_documents"], live["inserted"], live["history"])))
    finally:
        session.rollback()
        session.close()


# ------------------------------------------------ M5, bare 1 and 0 as a probability
def m5() -> None:
    from app.risk_values import RiskProbability, ValueRefusal, parse_probability

    print()
    print("M5. bare 1 and 0 refuse as a probability, exactly as 2 through 5 do")

    def _kind(cell, **kw):
        return parse_probability(cell, **kw)

    for cell in ("1", "0"):
        r = _kind(cell)
        check(f"bare {cell!r} refuses with no scale stated", isinstance(r, ValueRefusal),
              type(r).__name__ + " " + str(getattr(r, "value", "")))
    # The reason it refuses with is the SAME reason 2 through 5 refuse with. If the two
    # diverged, one of them would be a special case rather than one rule.
    check("the refusal reason is the one 2 through 5 already give",
          getattr(_kind("1"), "reason", None) == getattr(_kind("5"), "reason", ""))
    # A fraction is written with a decimal point, and every one of those still reads.
    for cell, want in ((".4", 0.4), ("0.4", 0.4), ("1.0", 1.0), ("0.0", 0.0), ("0.999", 0.999)):
        r = _kind(cell)
        check(f"{cell!r} still reads as {want}",
              isinstance(r, RiskProbability) and r.value == want, str(r))
    # A stated unit still reads, and a stated 1 per cent is no longer certainty.
    check("'100%' still reads as 1.0", _kind("100%").value == 1.0)
    check("'1 %' reads as 0.01, not as certainty", _kind("1 %").value == 0.01)
    check("a percent COLUMN reads a bare '1' as 0.01, not as certainty",
          _kind("1", column_is_percent=True).value == 0.01,
          str(_kind("1", column_is_percent=True)))
    check("a percent COLUMN still reads a bare '30' as 0.3",
          _kind("30", column_is_percent=True).value == 0.3)
    # A band word is untouched by any of this.
    check("'Low' is still a band, not a number", _kind("Low").band == "Low")


# ---------------------------------- the two small ones named in the owner's order
def small() -> None:
    from app.compliance_register import _HEADINGS
    from app.extraction_client import describe_json_truncation

    print()
    print("Also in scope: the dead truncation suffix and the duplicated register heading")

    check("describe_json_truncation('') is None -- the branch the dead suffix depended on",
          describe_json_truncation("") is None)
    seen: dict[str, str] = {}
    dupes: list[str] = []
    for field, headings in _HEADINGS.items():
        for h in headings:
            if h in seen:
                dupes.append(f"{h}: {seen[h]} and {field}")
            seen[h] = field
    check("no heading is claimed by two register fields", not dupes, "; ".join(dupes))
    check("'status' is still read, by exactly one field",
          seen.get("status") == "status", str(seen.get("status")))
    # What the duplicate COST: a closure-status-only register made every row both assessed and
    # satisfied, because `_row` derives `assessed` from `satisfied` when no assessed column was
    # printed. A workflow state is not a conformance outcome.
    from app.compliance_register import _row
    r = _row({"Requirement ID": "R1", "Status": "Closed"})
    check("a status-only register yields no `satisfied` and is NOT assessed",
          "satisfied" not in r and r.get("assessed") is False, repr(r))
    check("the status text is still carried, verbatim", r.get("status") == "Closed", repr(r))
    # A closed nonconformance that FAILED reads as failed, not as satisfied.
    r = _row({"Requirement ID": "R2", "Result": "Fail", "Status": "Closed"})
    check("a CLOSED but FAILED row is satisfied False, not True",
          r.get("satisfied") is False and r.get("assessed") is True, repr(r))
    # A register that means to state an outcome still states one.
    r = _row({"Requirement ID": "R3", "Result": "Pass"})
    check("a stated outcome column still reads",
          r.get("satisfied") is True and r.get("assessed") is True, repr(r))


def main() -> int:
    h5()
    m4()
    h3_r3()
    h4()
    m5()
    small()
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
