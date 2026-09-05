#!/usr/bin/env python3
"""
RUN 138, TASK 2. THE ASSEMBLY AND COMPUTATION TESTS, TAKEN BEFORE THE CORPUS IS REASSEMBLED.

T1..T8 of the Run 138 order, each asserted against the PRODUCTION code paths --
`extraction_merge.assemble_signal_inputs` / `select_signal_inputs`, and the A1.x modules in
`simulation/models_evm.py` -- never against a re-implementation of them.

Every expectation below names the source it is derived from, in a comment beside it (rule R2:
a test expectation is independent of the implementation it checks). Where the expectation is
arithmetic on this file's own fixture figures, the arithmetic is written out rather than read
off the code under test.

RUN IT WITH cwd = server/ .  T1..T7 need no database and make no model call: the assembler and
the modules are pure.  T8 needs a THROWAWAY SQLite DATABASE_URL, already migrated:

    export DATABASE_URL=sqlite:////abs/path/scratch.db
    python -m alembic upgrade head
    python tools/test_run138_assembly_and_precision.py

Without DATABASE_URL, T8 reports BLOCKED (counted as neither pass nor fail, and the fact is
printed) rather than passing vacuously.

WHAT THIS FILE WRITES: nothing, unless --write-artifact is given, and then only the T7 sweep
table, routed through the Run 135C `.artifact_scratch` mechanism (`tools/artifact_write.py`).
The T8 database work is rolled back and never committed.
"""
from __future__ import annotations

import copy
import os
import pathlib
import sys
from datetime import date

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))

from app.extraction_merge import (  # noqa: E402
    _NUMERIC_EMISSIONS, _round3, assemble_signal_inputs, emit_observations,
    select_signal_inputs,
)
from app.field_registry import IDENTITY_FIELDS, WRITER_TIERS  # noqa: E402
from app.simulation.models import SIMULATION_VERSION, check_inputs  # noqa: E402
from app.simulation.models_evm import (  # noqa: E402
    run_bayesian_eac, run_earned_schedule, run_tcpi, run_vac,
)
from artifact_write import artifact_out, repo_root  # noqa: E402


def RAND() -> float:
    """The modules take a callable for the stochastic branches; none reached here uses it."""
    return 0.5


CUTOFF = date(2025, 1, 31)

ok = fail = 0
blocked: list[str] = []


def _brief(v) -> str:
    """A repr short enough to read. Only the PRINTING is abbreviated; the comparison is whole."""
    s = repr(v)
    return s if len(s) <= 160 else s[:157] + "..."


def check(label: str, got, want) -> None:
    global ok, fail
    if got == want:
        ok += 1
        print(f"  PASS  {label}: {_brief(got)}")
    else:
        fail += 1
        print(f"  FAIL  {label}: got {_brief(got)}, expected {_brief(want)}")


def block(label: str, why: str) -> None:
    blocked.append(f"{label}: {why}")
    print(f"  BLOCKED  {label}: {why}")


def doc(sha, dt, ex, document_id=None):
    return {"sha256": sha, "doc_type": dt, "filename": sha + ".pdf",
            "document_id": document_id or ("DOC-" + sha.upper()), "extraction": ex}


# --------------------------------------------------------------------------- the fixture
#
# PRJ-002 period 1, as the corpus documents state it (the same figures the Run 132 suite
# carries). The pay application's `amount_paid_to_date` is earned value LESS TEN PER CENT
# RETAINAGE: 1,815,000 x 0.90 = 1,633,500. That identity is ASSERTED in T4 rather than assumed,
# so the retainage premise is measured on the fixture itself.
#
# The monthly report's as-of key is `report_date`. SOURCE: the monthly_report field list in
# `app/extraction_fields.py:392`, which names `report_date` and not `report_period` -- the
# Run 132 fixture uses `report_period`, which is not a monthly_report field at all, so its ac
# carries no as-of. See the Run 138A report for that finding.
MR = doc("mr1", "monthly_report", {
    "actual_cost": 1900000, "earned_value": 1815000, "planned_value": 1900000,
    "actual_percent_complete": 60.5, "planned_percent_complete": 63.3,
    "budget_at_completion": 3000000, "report_date": "2025-01-31"})
PA = doc("pa1", "pay_application", {
    "amount_paid_to_date": 1633500, "completed_to_date": 1815000,
    "percent_complete_verified": 60.5, "original_contract_sum": 3000000,
    "original_contingency": 150000, "remaining_contingency": 90000,
    "period_to_date": "2025-01-31"})

EV = 1815000            # the value of work performed, stated identically by both documents
AC_STATED = 1900000     # the monthly report's stated actual cost
PAID = 1633500          # the pay application's amount released, net of retainage


# =========================================================================== T1
print("\nT1. Both a pay application and a monthly report present.")
both = assemble_signal_inputs([MR, PA])
# SOURCE: the Run 132 order -- actual cost comes from the document that states an actual cost.
check("T1 ac", both["ac"], AC_STATED)
check("T1 ac provenance docType", both["sources"]["ac"]["docType"], "monthly_report")
# SOURCE: the definition of CPI, EV/AC, applied to this fixture's own two stated figures.
# Written out here so the expectation does not read the assembler's own quotient back.
check("T1 cpi is EV/AC of the monthly report", both["cpi"], EV / AC_STATED)
check("T1 cpi is NOT EV/amount-paid", both["cpi"] == EV / PAID, False)
# SOURCE: the Run 138 invariant -- every selected ac carries document type, document id,
# as-of period and extraction reference. The content hash IS the version identity here; see
# `_source_entry`'s docstring on content-addressed storage.
src = both["sources"]["ac"]
check("T1 ac documentId", src.get("documentId"), "DOC-MR1")
check("T1 ac documentVersion (sha256)", src.get("documentVersion"), "mr1")
check("T1 ac asOf", src.get("asOf"), "2025-01-31")
# THE ONE PART OF THAT INVARIANT MAIN DOES NOT MEET, ASSERTED ANYWAY SO THE GAP IS ON RECORD.
# The order requires the selected ac to carry its SOURCE FIELD -- the raw extraction key the
# figure was read from, `actual_cost`. `emit_observations` does not put the raw key on the
# observation, so `_source_entry` cannot record it. THIS CHECK FAILS ON MAIN. It is a finding,
# not a broken test; closing it means editing `app/extraction_merge.py`, which Run 138 agent A
# does not own.
check("T1 ac sourceField (KNOWN GAP, see report)", src.get("sourceField"), "actual_cost")


# =========================================================================== T2
print("\nT2. Pay application only -- ac absent, and every ac-dependent module abstains.")
pay_only = assemble_signal_inputs([PA])
check("T2 ac", pay_only["ac"], None)
check("T2 no provenance record for ac", "ac" in pay_only["sources"], False)
check("T2 cpi", pay_only["cpi"], None)
# SOURCE: `check_inputs` (simulation/models.py) is the declared EVM input check. It must fail
# CLEANLY -- return False -- not raise, and not default a value in.
check("T2 check_inputs(bac,ev,ac)", check_inputs(pay_only, ("bac", "ev", "ac")), False)
check("T2 check_inputs(ac)", check_inputs(pay_only, ("ac",)), False)
check("T2 check_inputs(bac,cpi)", check_inputs(pay_only, ("bac", "cpi")), False)
# SOURCE: the abstention contract in `insufficient()` -- status_color None, insufficient_data
# True. An abstaining module is never treated as Green.
for name, fn in (("TCPI/A1.7", run_tcpi), ("VAC/A1.8", run_vac),
                 ("EarnedSchedule/A1.6", run_earned_schedule),
                 ("BayesianEAC/A1.1", run_bayesian_eac)):
    out = fn(pay_only, RAND, CUTOFF)
    check(f"T2 {name} abstains", bool(out.get("insufficient_data")), True)
    check(f"T2 {name} status_color", out.get("status_color"), None)
    check(f"T2 {name} is not Green", out.get("status_color") == "Green", False)
# NO ZERO, NO CARRY-FORWARD, NO INTERPOLATION, NO INFERRED VALUE.
check("T2 ac is None, not 0", pay_only["ac"] is None and pay_only["ac"] != 0, True)
# SOURCE: `select_signal_inputs`'s `carried` contract -- ONLY identity-classified fields cross
# a period boundary (`field_registry.IDENTITY_FIELDS`). ac not being in that set is the
# STRUCTURAL reason no prior period's ac can carry forward, whatever a caller passes.
check("T2 'ac' is not an IDENTITY field", "ac" in IDENTITY_FIELDS, False)
prior_ac_obs = [o for o in emit_observations(MR) if o["field"] == "ac"]
check("T2 the prior period really did emit an ac to carry", len(prior_ac_obs), 1)
carried = select_signal_inputs(list(emit_observations(PA)), None, carried=prior_ac_obs)
check("T2 a prior period's ac does not carry forward", carried["ac"], None)
check("T2 no ac provenance from a carried observation", "ac" in carried["sources"], False)
# SOURCE: `_NUMERIC_EMISSIONS`, the single declaration of what each doc type may write. The
# pay application must emit no ac from ANY of its keys -- that is the Run 132 ruling.
check("T2 pay_application emits no ac",
      [raw for raw, f in _NUMERIC_EMISSIONS["pay_application"] if f == "ac"], [])


# =========================================================================== T3
print("\nT3. Monthly report only -- ac present, EVM eligible where the other inputs exist.")
mr_only = assemble_signal_inputs([MR])
check("T3 ac", mr_only["ac"], AC_STATED)
check("T3 ac provenance docType", mr_only["sources"]["ac"]["docType"], "monthly_report")
check("T3 cpi", mr_only["cpi"], EV / AC_STATED)
check("T3 check_inputs(bac,ev,ac)", check_inputs(mr_only, ("bac", "ev", "ac")), True)
check("T3 A1.8 does NOT abstain",
      bool(run_vac(mr_only, RAND, CUTOFF).get("insufficient_data")), False)
check("T3 A1.7 does NOT abstain",
      bool(run_tcpi(mr_only, RAND, CUTOFF).get("insufficient_data")), False)
# A1.6 Earned Schedule still abstains here, and correctly: it requires the time-phased planned
# value CURVE (`require_v3_structure`, models_evm.py), which no monthly report states. That is
# an absent STRUCTURE, not an absent actual cost.
check("T3 A1.6 still abstains for want of the PV curve, not for want of ac",
      bool(run_earned_schedule(mr_only, RAND, CUTOFF).get("insufficient_data")), True)


# =========================================================================== T4
print("\nT4. The retainage conflict -- identical BAC/EV/PV/period, two accounts of cost.")
check("T4 both documents state the same earned value",
      (MR["extraction"]["earned_value"], PA["extraction"]["completed_to_date"]), (EV, EV))
check("T4 both documents state the same budget",
      (MR["extraction"]["budget_at_completion"], PA["extraction"]["original_contract_sum"]),
      (3000000, 3000000))
check("T4 both documents cover the same period",
      (MR["extraction"]["report_date"], PA["extraction"]["period_to_date"]),
      ("2025-01-31", "2025-01-31"))
# SOURCE: the corpus's stated ten per cent retainage. Measured on the fixture, not assumed.
check("T4 amount paid IS earned value less ten per cent", PAID, EV * 0.9)
check("T4 amount paid is lower than the stated actual cost", PAID < AC_STATED, True)
check("T4 CPI comes from the monthly report", both["cpi"], EV / AC_STATED)
# THE FALSELY FAVOURABLE READING THE PAYMENT FIGURE WOULD PRODUCE, shown rather than described.
cpi_from_payment = EV / PAID
check("T4 the payment figure reads UNDER cost", cpi_from_payment > 1.0, True)
check("T4 the stated cost reads OVER cost", both["cpi"] < 1.0, True)
# SOURCE: A1.8's band ladder (`run_vac`, models_evm.py): Green at or above 0 per cent, which is
# a cost performance index of 1.00. Both bands are taken from the production module.
band_true = run_vac({"bac": 3000000, "cpi": both["cpi"]}, RAND, CUTOFF)["status_color"]
band_paid = run_vac({"bac": 3000000, "cpi": cpi_from_payment}, RAND, CUTOFF)["status_color"]
check("T4 A1.8 on the stated cost", band_true, "Yellow")
check("T4 A1.8 on the payment figure would be Green", band_paid, "Green")
check("T4 the two bands differ", band_true == band_paid, False)


# =========================================================================== T5
print("\nT5. actualPctComplete selection is unchanged, and deliberately so.")
print("    Retention reduces the PAYMENT, never the PERCENTAGE certified. "
      "`percent_complete_verified` is the certified figure on the G702, independently "
      "verified before any retention is withheld, and it is the same quantity as the monthly "
      "report's `actual_percent_complete`. So the pay application keeps tier 0 for this field, "
      "and only for this field.")
# SOURCE: the recorded decision at field_registry.py:236-239.
check("T5 actualPctComplete tiers", WRITER_TIERS.get("actualPctComplete"),
      {"pay_application": 0, "monthly_report": 1})
check("T5 actualPctComplete comes from the pay application",
      both["sources"]["actualPctComplete"]["docType"], "pay_application")
check("T5 actualPctComplete value", both["actualPctComplete"], 60.5)
# SOURCE: the Run 132 comment at field_registry.py:214 -- ac must not regain a writer tier.
check("T5 ac has no writer tier", "ac" in WRITER_TIERS, False)


# =========================================================================== T6
print("\nT6. CPI precision -- a true index in [0.9995, 1.0) is stored unrounded, and bands "
      "from the unrounded value.")
# 9,995 / 10,000 = 0.9995 exactly: inside the interval, and the first value that half-up
# rounding at three decimals lifts to 1.0.
T6 = assemble_signal_inputs([doc("mr6", "monthly_report", {
    "earned_value": 9995, "actual_cost": 10000, "budget_at_completion": 3000000,
    "report_date": "2025-01-31"})])
check("T6 stored cpi is the exact quotient", T6["cpi"], 9995 / 10000)
check("T6 stored cpi is in [0.9995, 1.0)", 0.9995 <= T6["cpi"] < 1.0, True)
check("T6 stored cpi is not the rounded figure", T6["cpi"] == _round3(T6["cpi"]), False)
# BEFORE THE RUN 135 FIX the assembler stored `_round3(ev/ac)`. Both bands below are taken
# from the production module, on the two stored values, so the difference is MEASURED.
before = run_vac({"bac": 3000000, "cpi": _round3(9995 / 10000)}, RAND, CUTOFF)
after = run_vac({"bac": 3000000, "cpi": T6["cpi"]}, RAND, CUTOFF)
check("T6 the pre-Run-135 stored cpi", _round3(9995 / 10000), 1.0)
check("T6 A1.8 band BEFORE the fix (rounded, favourable)", before["status_color"], "Green")
check("T6 A1.8 band AFTER the fix (unrounded)", after["status_color"], "Yellow")
check("T6 the fix changed the band", before["status_color"] == after["status_color"], False)
# SOURCE: A1.8's own canonical quantity, VAC% = (1 - 1/CPI) x 100, written out here.
check("T6 vac_pct after the fix", after["vac_pct"], (1 - 1 / (9995 / 10000)) * 100)


# =========================================================================== T7
print("\nT7. A1.8 edge -- CPI exactly 0.90 bands identically across a budget sweep.")
# 200 budgets log-spaced from $1,000 to $200,000,000: the Run 135 sweep's endpoints, sampled.
LO, HI, N = 1_000.0, 200_000_000.0, 200
budgets = [LO * (HI / LO) ** (i / (N - 1)) for i in range(N)]
rows = [(b, run_vac({"bac": b, "cpi": 0.90}, RAND, CUTOFF)) for b in budgets]
colors = {r["status_color"] for _b, r in rows}
pcts = {r["vac_pct"] for _b, r in rows}
check("T7 budgets swept", len(budgets), N)
check("T7 exactly one band across the sweep", len(colors), 1)
# SOURCE: the A1.8 ladder -- `amber_at_or_above` is (1 - 1/0.90) x 100, and a CPI of exactly
# 0.90 IS that edge, which is inclusive, so the band is Amber.
check("T7 that band is Amber", colors, {"Amber"})
check("T7 exactly one vac_pct across the sweep", len(pcts), 1)
check("T7 vac_pct is the canonical quantity", pcts, {(1 - 1 / 0.90) * 100})
check("T7 the budget is absent from the banded quantity",
      all(r["vac_pct"] == (1 - 1 / 0.90) * 100 for _b, r in rows), True)
# The DOLLAR figure does depend on the budget, and must: it is money, not an index.
check("T7 the dollar VAC does vary with the budget",
      len({r["vac"] for _b, r in rows}) > 1, True)

# The sweep table, routed through the Run 135C mechanism: it lands under `.artifact_scratch/`
# and the committed path is untouched unless --write-artifact is given deliberately.
_sweep = artifact_out(repo_root() / "code_audit" / "run138_a18_bac_sweep.csv")
_sweep.write_text("bac,cpi,vac_pct,band\n" + "".join(
    f"{b!r},0.9,{r['vac_pct']!r},{r['status_color']}\n" for b, r in rows), encoding="utf-8")
print(f"  (T7 sweep table written to {_sweep})")


# =========================================================================== T8
print("\nT8. No historical rewrite -- a recompute writes a NEW row and changes nothing.")
if not os.environ.get("DATABASE_URL"):
    block("T8", "DATABASE_URL is unset. T8 needs a throwaway migrated SQLite file; it is not "
                "assertable without one and is not asserted vacuously.")
else:
    import app.main as _main  # noqa: E402  binds the engine to DATABASE_URL
    from app.documents import run_and_store  # noqa: E402
    from app.models import Project  # noqa: E402
    from app.research_models import ComputedResult, new_ulid  # noqa: E402
    from sqlalchemy import select as _select  # noqa: E402

    with _main.SessionFactory() as s:
        proj = Project(legacy_id="RUN138A-T8", doc={"id": "RUN138A-T8", "name": "Run 138 T8"})
        s.add(proj)
        s.flush()

        SOURCE_DOCS = [{"document_id": "DOC-MR1", "sha256": "mr1",
                        "doc_type": "monthly_report", "filename": "mr1.pdf"}]
        first = run_and_store(s, proj, 1, dict(mr_only), CUTOFF,
                              source_documents=SOURCE_DOCS)["row"]
        s.flush()
        # A PRIOR-RUN ROW LOOKS LIKE THIS: an older simulation version stamped on it. Set
        # directly, because what is under test is that the NEW row is DISTINGUISHABLE from a
        # row carrying an older version -- not how that older row came to exist.
        first.simulation_version = "sim-2026.09-v69"
        s.flush()
        # SNAPSHOT THE PRIOR ROW AS THE DATABASE HOLDS IT, not as the ORM object in memory
        # holds it: JSON storage turns tuples into lists, and comparing an in-memory copy with
        # a reloaded row would report that difference as a rewrite. Both sides of every
        # "unchanged" check below are therefore rows read back out of the database.
        old_id = first.result_id
        s.expunge_all()
        first = s.scalars(_select(ComputedResult)
                          .where(ComputedResult.result_id == old_id)).first()
        old_version = first.simulation_version
        old_si = copy.deepcopy(first.signal_inputs)
        old_modules = copy.deepcopy(first.module_results)
        old_status = first.project_status
        old_sources = copy.deepcopy(first.source_documents)
        old_computed_at = first.computed_at

        # THE PRODUCTION RECOMPUTE ORDER, from `a_adminrecompute` / `_compute_and_store`: mint
        # the new id, mark the outgoing row superseded, THEN insert. `uq_computed_results_one_live`
        # permits exactly one live row per (project, period).
        new_id = new_ulid()
        first.superseded_by = new_id
        s.flush()
        second = run_and_store(s, proj, 1, dict(mr_only), CUTOFF,
                               source_documents=SOURCE_DOCS, result_id=new_id)["row"]
        s.flush()

        # DETACH EVERYTHING AND READ THE ROWS BACK OUT OF THE DATABASE. Without this, `prior`
        # would be the SAME PYTHON OBJECT as `first` and every "unchanged" check below would be
        # comparing a value with itself -- a check that cannot fail is worse than no check.
        new_row_id = second.result_id
        s.expunge_all()
        prior = s.scalars(_select(ComputedResult)
                          .where(ComputedResult.result_id == old_id)).first()
        second = s.scalars(_select(ComputedResult)
                           .where(ComputedResult.result_id == new_row_id)).first()
        check("T8 the prior row is still readable", prior is not None, True)
        check("T8 prior signal inputs unchanged", prior.signal_inputs, old_si)
        check("T8 prior module results unchanged", prior.module_results, old_modules)
        check("T8 prior project status unchanged", prior.project_status, old_status)
        check("T8 prior source documents unchanged", prior.source_documents, old_sources)
        check("T8 prior computed_at unchanged", prior.computed_at, old_computed_at)
        check("T8 prior version unchanged", prior.simulation_version, old_version)
        check("T8 nothing overwritten in place: two rows exist",
              len(s.scalars(_select(ComputedResult)
                            .where(ComputedResult.project_id == proj.id)).all()), 2)
        check("T8 the new row has a distinct identity", second.result_id != old_id, True)
        check("T8 the prior row names its successor", prior.superseded_by, second.result_id)
        check("T8 the new row is the live one", second.superseded_by, None)
        # SOURCE: `SIMULATION_VERSION` (simulation/models.py) -- the version a run stamps.
        check("T8 the new row carries the v70 version", second.simulation_version,
              SIMULATION_VERSION)
        check("T8 the new version differs from the prior one",
              second.simulation_version == old_version, False)
        check("T8 the new row carries its own provenance identity",
              bool(second.source_documents) and second.seed is not None
              and second.period_cutoff == CUTOFF, True)
        # Nothing is committed: this suite leaves no row behind.
        s.rollback()


total = ok + fail
print(f"\nRESULT: {ok}/{total} checks passed")
if blocked:
    print(f"BLOCKED: {len(blocked)}")
    for b in blocked:
        print(f"  {b}")
raise SystemExit(1 if fail else 0)
