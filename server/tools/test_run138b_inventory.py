"""RUN 138B, TASK 1. THE AFFECTED-PERIOD CLASSIFIER, AND THE INVENTORY IT PRODUCES.

Two things, deliberately in one file, because a count is worthless without the rule that
produced it.

  1. `classify(row)` -- the owner's four-way classification, executable, from a stored
     `computed_results` row alone. Checked below against constructed rows on every arm and on
     both sides of each edge, so a wrong classification fails here rather than in an inventory.
  2. The inventory itself, run over whatever corpus `DATABASE_URL` points at. It reports the
     row count first, so an EMPTY corpus reports as empty rather than as "nothing affected".

Run with cwd = server/ and DATABASE_URL pointing at a THROWAWAY SQLite file or a clone. It
opens a read-only session: it SELECTs and never writes. No model call.
"""
from __future__ import annotations

import os
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

ok = fail = 0


def check(label, got, want):
    global ok, fail
    if got == want:
        ok += 1
        print(f"  PASS  {label}: {got!r}")
    else:
        fail += 1
        print(f"  FAIL  {label}: got {got!r}, expected {want!r}")


# --------------------------------------------------------------------------- the rule

#: A stored value is a rounded one when it is EXACTLY the half-up three-place rounding of the
#: quotient its own row states. That is the whole test the Run 135 H1 correction needs: the
#: stored field either equals ev/ac or it does not.
def _round3(v: float) -> float:
    import math
    return math.floor(v * 1000 + 0.5) / 1000


def stored_cpi_is_rounded(si: dict) -> bool | None:
    """None where it cannot be decided: no cpi stored, or no ev/ac to divide."""
    cpi, ev, ac = si.get("cpi"), si.get("ev"), si.get("ac")
    if cpi is None or ev is None or ac in (None, 0):
        return None
    return cpi != ev / ac


def ac_source_doc_type(si: dict) -> str | None:
    return ((si.get("sources") or {}).get("ac") or {}).get("docType")


#: Modules whose ARITHMETIC changed at Runs 135/136 with no change to their inputs. A period
#: touching any of these needs recomputation even when its signal inputs are already correct.
ARITHMETIC_ONLY_MODULES = ("A1.8", "A3.4", "C1.3", "A2.12", "B2.18", "B2.19", "H6", "H7")


def classify(row: dict) -> tuple[str, list[str]]:
    """(classification, corrections that apply) for one stored computed_results row.

    ``row`` is {signal_inputs, module_results, is_training}. Exactly one classification.
    """
    si = dict(row.get("signal_inputs") or {})
    corrections: list[str] = []

    if row.get("is_training"):
        # The training path never selects `ac` from a document -- the engine holds it in state --
        # so Run 132 does not apply to it. F2 and F3 do, and they reach all three artefacts.
        corrections.append("Run 136 F2/F3 (training_engine, training_debrief CPI rounding "
                           "and half-to-even _round3)")
        return "training_period", corrections

    src = ac_source_doc_type(si)
    rounded = stored_cpi_is_rounded(si)
    if src == "pay_application":
        corrections.append("Run 132 (pay application supplied ac)")
    if rounded is True:
        corrections.append("Run 135 H1 (cpi rounded before storage)")
    if corrections:
        return "reassembly_required", corrections

    banded = {m.get("module_id") for m in (row.get("module_results") or [])}
    hit = [m for m in ARITHMETIC_ONLY_MODULES if m in banded]
    if hit:
        corrections.append("module arithmetic only: " + ", ".join(hit))
        return "recompute_only", corrections

    return "unaffected", corrections


CLASSIFICATIONS = ("reassembly_required", "recompute_only", "training_period", "unaffected")


# --------------------------------------------------------------------------- the rule, proved

print("=== the classifier, on constructed rows ===")


def row(si, mods=(), training=False):
    return {"signal_inputs": si, "module_results": [{"module_id": m} for m in mods],
            "is_training": training}


_PAY = {"ev": 1815000, "ac": 1633500, "cpi": 1815000 / 1633500,
        "sources": {"ac": {"docType": "pay_application"}}}
_MR = {"ev": 1815000, "ac": 1900000, "cpi": 1815000 / 1900000,
       "sources": {"ac": {"docType": "monthly_report"}}}
_MR_ROUNDED = dict(_MR, cpi=_round3(1815000 / 1900000))

check("pay-application ac -> reassembly", classify(row(_PAY))[0], "reassembly_required")
check("monthly-report ac, unrounded cpi, no arithmetic module -> unaffected",
      classify(row(_MR))[0], "unaffected")
check("monthly-report ac, ROUNDED cpi -> reassembly",
      classify(row(_MR_ROUNDED))[0], "reassembly_required")
check("correct inputs + A1.8 banded -> recompute only",
      classify(row(_MR, ("A1.7", "A1.8")))[0], "recompute_only")
check("correct inputs + B2.18 banded -> recompute only",
      classify(row(_MR, ("B2.18",)))[0], "recompute_only")
check("training row -> training period whatever its inputs",
      classify(row(_MR, ("A1.8",), training=True))[0], "training_period")
check("training row is training even with a pay-application ac",
      classify(row(_PAY, training=True))[0], "training_period")
check("no ac at all (EVM abstained) -> unaffected, nothing to reselect",
      classify(row({"ev": 1815000, "ac": None, "cpi": None, "sources": {}}))[0], "unaffected")
# THE EDGE THE ROUNDING TEST MUST GET RIGHT: a quotient that is ALREADY three-place exact is
# not evidence of rounding, and must not be classified as such.
_EXACT = {"ev": 1000.0, "ac": 2000.0, "cpi": 0.5, "sources": {"ac": {"docType": "monthly_report"}}}
check("cpi that is exactly its own quotient is not 'rounded'",
      stored_cpi_is_rounded(_EXACT), False)
check("...and classifies unaffected", classify(row(_EXACT))[0], "unaffected")
# ...and the favourable edge Run 135 H1 named, 0.9995 -> 1.0, IS caught.
_H1 = {"ev": 0.9995, "ac": 1.0, "cpi": 1.0, "sources": {"ac": {"docType": "monthly_report"}}}
check("the H1 favourable edge (true 0.9995 stored 1.0) is caught",
      classify(row(_H1))[0], "reassembly_required")
check("rounding undecidable with no cpi", stored_cpi_is_rounded({"ev": 1, "ac": 2}), None)

# --------------------------------------------------------------------------- the inventory

print("\n=== the inventory, over the corpus DATABASE_URL names ===")
url = (os.environ.get("DATABASE_URL") or "").strip()
print(f"DATABASE_URL scheme: {url.split(':', 1)[0] if url else '(unset)'}")
if url.startswith("postgres"):
    print("REFUSED: this script is not run against Postgres by this run. Point DATABASE_URL at "
          "a throwaway SQLite file or a clone.")
    raise SystemExit(2)

counts = dict.fromkeys(CLASSIFICATIONS, 0)
total = 0
if not url:
    print("No DATABASE_URL: no corpus to inventory.")
else:
    from sqlalchemy import create_engine, text
    eng = create_engine(url)
    with eng.connect() as conn:
        total = conn.execute(text("select count(*) from computed_results")).scalar_one()
        print(f"computed_results rows: {total}")
        if total:
            import json
            rows = conn.execute(text(
                "select c.project_id, c.period, c.signal_inputs, c.module_results, "
                "c.simulation_version, p.legacy_id, p.is_training "
                "from computed_results c join projects p on p.id = c.project_id "
                "where c.superseded_by is null order by p.legacy_id, c.period")).all()
            print(f"{'project':<12}{'per':>4}  {'prior ac':>14}  {'ac source':<16}"
                  f"{'prior cpi':>22}  classification")
            for pid, period, si, mods, ver, legacy, training in rows:
                si = json.loads(si) if isinstance(si, str) else (si or {})
                mods = json.loads(mods) if isinstance(mods, str) else (mods or [])
                cls, why = classify({"signal_inputs": si, "module_results": mods,
                                     "is_training": training})
                counts[cls] += 1
                print(f"{legacy:<12}{period:>4}  {str(si.get('ac')):>14}  "
                      f"{str(ac_source_doc_type(si)):<16}{str(si.get('cpi')):>22}  "
                      f"{cls}  [{'; '.join(why)}]")

print("\nCounts by classification:")
for c in CLASSIFICATIONS:
    print(f"   {c:<22} {counts[c]}")
print(f"   {'TOTAL':<22} {total}")
if total == 0:
    print("\nTHE HONEST READING: this corpus holds NO stored computed result. There is nothing "
          "here to reassemble, recompute, compare or requalify. It is not evidence that "
          "production holds none.")

print(f"\n{ok} passed, {fail} failed")
print(f"RESULT: {ok}/{ok + fail} checks passed")
raise SystemExit(1 if fail else 0)
