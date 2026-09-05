"""Run 142A. PRJ-002 period 2's SHAPE, reconstructed on a throwaway database.

Standalone check-script, not pytest. Run with cwd = <worktree>/server and DATABASE_URL
pointing at a throwaway SQLite file.

    export DATABASE_URL=sqlite:////abs/path/r142a.db
    python -m alembic upgrade head
    python tools/test_run142a_endtoend.py

THE STORED ROWS ARE NOT REACHABLE. PRJ-002 does not exist on any database this run may touch:
production Postgres is never contacted, and the untracked `server/dev.db` is a stale August
database at sim-2026.08-v42 carrying no PRJ-002. So this constructs an EQUIVALENT FIXTURE --
a computed row whose A3 category has four modules that ran and abstained with their reasons
and NO A3 key in `category_statuses`, which is exactly the shape `simulation.compute` produces
for a category in which nothing banded -- and says so plainly rather than implying otherwise.
"""
from __future__ import annotations
import os, sys, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from sqlalchemy import select                              # noqa: E402
import app.main as _main                                  # noqa: E402
from app.models import Project                             # noqa: E402
from app.research_identity import new_ulid                 # noqa: E402
from app.research_models import ComputedResult             # noqa: E402
from app import documents, research_export                 # noqa: E402

PID = "RUN142A"

A3_ABSTAINED = [
    {"module_id": "A3.2", "category": "A3", "group": "A",
     "abstention_reason": "awaiting a cost risk model",
     "abstention_reason_code": "missing_required_input",
     "evidence_metric": "awaiting a cost risk model"},
    {"module_id": "A3.3", "category": "A3", "group": "A",
     "abstention_reason": "beneath the configured exposure floor",
     "abstention_reason_code": "no_exposure",
     "evidence_metric": "beneath the configured exposure floor"},
    {"module_id": "A3.5", "category": "A3", "group": "A",
     "abstention_reason": "awaiting a contingency drawdown history",
     "abstention_reason_code": "insufficient_history",
     "evidence_metric": "awaiting a contingency drawdown history"},
    {"module_id": "A3.6", "category": "A3", "group": "A",
     "abstention_reason": "awaiting a risk register",
     "abstention_reason_code": "missing_required_input",
     "evidence_metric": "awaiting a risk register"},
]
A1_COMPUTED = [{"module_id": "A1.2", "category": "A1", "group": "A",
                "status_color": "Green", "evidence_metric": "CPI 1.02"}]
CATS = {"A1": {"status": "Green", "state": "computed",
               "contributes_to_project_status": True}}


def seed(period: int, abstained):
    with _main.SessionFactory() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PID))
        if proj is None:
            proj = Project(legacy_id=PID, doc={"id": PID, "name": "Run 142A reconstruction"})
            s.add(proj)
            s.commit()
            proj = s.scalar(select(Project).where(Project.legacy_id == PID))
        for old in s.scalars(select(ComputedResult).where(
                ComputedResult.project_id == proj.id, ComputedResult.period == period)):
            s.delete(old)
        s.commit()
        s.add(ComputedResult(
            result_id=new_ulid(), project_id=proj.id, period=period,
            signal_inputs={}, module_results=list(A1_COMPUTED), category_statuses=dict(CATS),
            project_status=None, portfolio_snapshot=None,
            simulation_version="run142a-fixture", seed=1, period_cutoff=__import__("datetime").date(2026, 9, 1),
            source_documents=[], abstained=list(abstained)))
        s.commit()


def view(period: int):
    with _main.SessionFactory() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PID))
        row = s.scalar(select(ComputedResult).where(
            ComputedResult.project_id == proj.id, ComputedResult.period == period))
        return documents._result_view(row, include_recommendation=True,
                                      project_legacy_id=PID)


def export_rows():
    with _main.SessionFactory() as s:
        return [r for r in research_export.build_module_results_rows(s, {PID}, None, None)]


fail = 0
seed(1, A3_ABSTAINED)          # every A3 module ran and abstained
seed(2, [])                    # no A3 module dispatched

v1, v2 = view(1), view(2)


def a3_of(v, field):
    return [r for r in (v.get(field) or [])
            if str(r.get("category") or str(r.get("module_id") or "").split(".")[0]) == "A3"]


d1 = {d["category"]: d for d in v1["project_status_basis"]["required_missing_detail"]}
d2 = {d["category"]: d for d in v2["project_status_basis"]["required_missing_detail"]}
n1, n2 = len(a3_of(v1, "abstained")), len(a3_of(v2, "abstained"))

print("PROOF 7 -- PRJ-002 period 2's SHAPE on a throwaway database (equivalent fixture; the")
print("           real stored rows are not reachable from this run -- see the docstring).")
print("  served view, all-abstained fixture : %d A3 rows, reasons=%s"
      % (n1, [r.get("abstention_reason") for r in a3_of(v1, "abstained")]))
print("  served view, never-dispatched      : %d A3 rows" % n2)
print("  a3 posture, all-abstained          : %r"
      % ((v1["category_statuses"].get("A3") or {}).get("status"),))
print("  project_status                     : %r / %r"
      % (v1["project_status"], v2["project_status"]))
print("  a3 required_missing_detail (abst)  : %s" % (d1.get("A3"),))
print("  a3 required_missing_detail (never) : %s" % (d2.get("A3"),))
print("  status_reason, a3 clause (abst)    : %s"
      % [p for p in (v1["project_status_basis"]["status_reason"] or "").split(";")
         if "(a3)" in p.lower()])
print("  status_reason, a3 clause (never)   : %s"
      % [p for p in (v2["project_status_basis"]["status_reason"] or "").split(";")
         if "(a3)" in p.lower()])

if n1 != 4:
    print("FAIL proof 7: the served view carries %d A3 rows, expected 4" % n1); fail += 1
if n2 != 0:
    print("FAIL proof 7: never-dispatched fixture carries %d A3 rows, expected 0" % n2); fail += 1
if (v1["category_statuses"].get("A3") or {}).get("status"):
    print("FAIL proof 4: a posture was manufactured for a3"); fail += 1
if v1["project_status"] != v2["project_status"] or \
        v1["project_status_basis"]["official"] or v2["project_status_basis"]["official"]:
    print("FAIL proof 4: the project status moved or became official"); fail += 1
if d1.get("A3") == d2.get("A3"):
    print("FAIL proof 2: the two cases are indistinguishable on the card"); fail += 1

# ---------------------------------------------------------------- PROOF 6, THE EXPORTS
print()
print("PROOF 6 -- the exports carry what the card shows.")
# The export names the module by its REGISTRY NAME, not its id, so the A3 rows are identified
# as the period-1 rows that carry no status_color and an abstention reason code -- which is
# exactly the four abstentions this fixture stored. The A1 row that computed is excluded by
# the status_color test.
_rows = export_rows()
ex_a3 = [r for r in _rows if r.get("period") == 1
         and not r.get("status_color") and r.get("abstention_reason_code")]
ex_p2 = [r for r in _rows if r.get("period") == 2
         and not r.get("status_color") and r.get("abstention_reason_code")]
card_ids = sorted(r["module_id"] for r in a3_of(v1, "abstained"))
card_codes = sorted(r["abstention_reason_code"] for r in a3_of(v1, "abstained"))
print("  A3 module ids on the card   (%d): %s" % (len(card_ids), card_ids))
print("  abstaining export rows, all-abstained fixture (%d): %s"
      % (len(ex_a3), sorted(r["computation"] for r in ex_a3)))
print("  their reason codes in the export: %s"
      % sorted(str(r.get("abstention_reason_code")) for r in ex_a3))
print("  abstaining export rows, never-dispatched fixture (%d)" % len(ex_p2))
if len(ex_a3) != len(card_ids):
    print("FAIL proof 6: export carries %d abstaining rows, the card shows %d"
          % (len(ex_a3), len(card_ids)))
    fail += 1
elif sorted(str(r.get("abstention_reason_code")) for r in ex_a3) != card_codes:
    print("FAIL proof 6: the export's reason codes differ from the card's"); fail += 1
elif len(ex_p2) != 0:
    print("FAIL proof 6: the never-dispatched fixture exported %d abstaining rows"
          % len(ex_p2)); fail += 1
else:
    print("PASS proof 6: the export carries exactly the four rows the card now shows, with "
          "their reason codes, and none for the never-dispatched period. NOTE: the export "
          "reads the STORED row directly (research_export.build_module_results_rows) and "
          "therefore carried these four all along -- before this fix the export and the card "
          "DISAGREED, and they now agree.")

print()
print("RESULT:", "FAIL" if fail else "PASS", "(%d failing checks)" % fail)
sys.exit(1 if fail else 0)
