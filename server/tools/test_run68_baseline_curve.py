#!/usr/bin/env python3
"""
RUN 68. THE BASELINE-CURVE READER'S REFUSALS.

Run (from server/):

    PYTHONIOENCODING=utf-8 python tools/test_run68_baseline_curve.py

WHAT THIS SUITE IS FOR. `baseline_curve.read_baseline_curve` is the point where a printed table
becomes two governed structures, and every rule in it exists to stop a figure being manufactured
that the document never printed. Those rules are invisible from the outside: a curve summed out
of a periodic column, a blank period filled from its neighbours, or a falling curve quietly
sorted into order would all produce a module that COMPUTES, and a module that computes is exactly
what this programme is trying to produce -- which is why a wrong one would be believed.

So the refusals are pinned here, each with the figure that would have appeared had the reader
been permissive. A check that only asserted the happy path would pass on a reader that invents.

THIS SUITE ASSERTS THE READER, NOT THE MODEL. What a real extraction model returns for
`baseline_curve_json` is a separate question, guarded on the prompt side by
`test_extraction_prompt.py` section 2b.
"""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))


def finish() -> None:
    failed = [r for r in RESULTS if not r[0]]
    print(f"\nRESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    sys.exit(1 if failed else 0)


def section(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def main() -> None:
    from app.baseline_curve import read_baseline_curve as read

    section("1. THE ORDINARY TABLE IS READ AS PRINTED")

    rows = read([
        {"Period": 0, "Cumulative planned value (USD)": 0,
         "Cumulative planned spend (USD)": 0},
        {"Period": 1, "Cumulative planned value (USD)": "1,020,000",
         "Cumulative planned spend (USD)": "1,000,000"},
        {"Period": 2, "Cumulative planned value (USD)": "1,500,000",
         "Cumulative planned spend (USD)": "1,460,000"},
    ])
    check(len(rows) == 3, "every printed row is returned", str(len(rows)))
    check([r["cumulative_pv"] for r in rows] == [0.0, 1020000.0, 1500000.0],
          "the cumulative planned value is read, thousands separators and all")
    check([r["expected_spend"] for r in rows] == [0.0, 1000000.0, 1460000.0],
          "the cumulative planned spend is read as a SEPARATE curve from the value curve")
    check([r["period_index"] for r in rows] == [0.0, 1.0, 2.0]
          and all(r["index_basis"] == "stated" for r in rows),
          "the period index is the one the table states, and says so")

    section("2. A PERIODIC COLUMN IS NEVER READ AS A CUMULATIVE ONE")

    # THE DEFECT THIS FORBIDS. A baseline commonly prints both columns, and they differ by a
    # running sum. Had the reader accepted the periodic column here, period 2 would have carried
    # 480,000 instead of 1,500,000 -- a curve that FALLS, which `earned_schedule` would then
    # refuse for a reason that had nothing to do with the real fault.
    both = read([
        {"Period": 1, "Planned value this period (USD)": 1_020_000,
         "Cumulative planned value (USD)": 1_020_000},
        {"Period": 2, "Planned value this period (USD)": 480_000,
         "Cumulative planned value (USD)": 1_500_000},
    ])
    check([r["cumulative_pv"] for r in both] == [1020000.0, 1500000.0],
          "with both columns printed, the CUMULATIVE one is taken")
    check(all(r["cumulative_pv"] != 480000.0 for r in both),
          "the periodic figure never reaches the curve")

    # AND WHERE ONLY THE PERIODIC COLUMN IS PRINTED, NOTHING IS ASSEMBLED. Summing it here would
    # produce a cumulative curve the document does not contain, so the rows state no cumulative
    # quantity, are dropped, and the modules go on abstaining.
    periodic_only = read([
        {"Period": 1, "Planned value this period (USD)": 1_020_000},
        {"Period": 2, "Planned value this period (USD)": 480_000},
        {"Period": 3, "Incremental planned spend": 800_000},
        {"Period": 4, "Monthly planned cost": 800_000},
    ])
    check(periodic_only == [],
          "a table printing ONLY periodic columns yields no curve, and none is summed",
          str(periodic_only))

    section("3. NOTHING IS INTERPOLATED, FILLED, SORTED OR INVENTED")

    gapped = read([
        {"Period": 1, "Cumulative planned value": 1_020_000},
        {"Period": 2, "Cumulative planned value": ""},
        {"Period": 3, "Cumulative planned value": 2_300_000},
    ])
    check([r["cumulative_pv"] for r in gapped] == [1020000.0, 2300000.0],
          "a blank period is DROPPED, not filled from its neighbours")
    check(all(r["cumulative_pv"] != 1660000.0 for r in gapped),
          "the midpoint of the two neighbours appears nowhere")

    # A FALLING CURVE IS PASSED THROUGH AS PRINTED. `earned_schedule` refuses a baseline that
    # decreases, and that refusal is the correct outcome: a falling column means it was misread.
    # Sorting the figures here would hide the misreading behind a curve that passes the guard.
    falling = read([
        {"Period": 1, "Cumulative planned value": 3_000_000},
        {"Period": 2, "Cumulative planned value": 1_500_000},
    ])
    check([r["cumulative_pv"] for r in falling] == [3000000.0, 1500000.0],
          "a falling curve is returned as printed, for the canonical guard to refuse")

    totals = read([
        {"Period": 1, "Cumulative planned value": 1_020_000},
        {"Period": "Total", "Cumulative planned value": ""},
        {"Period": "", "Cumulative planned value": None},
    ])
    check(len(totals) == 1, "a totals row and a blank row state no figure and are dropped",
          str(totals))

    section("4. NO PERIOD INDEX IS INVENTED, AND A DERIVED ONE SAYS SO")

    unindexed = read([
        {"Cumulative planned value": 1_020_000},
        {"Cumulative planned value": 1_500_000},
    ])
    check([r["period_index"] for r in unindexed] == [1.0, 2.0],
          "with no index column the rows' own PRINTED ORDER supplies it")
    check(all(r["index_basis"] == "printed order" for r in unindexed),
          "and the structure records that it was the printed order, not a stated index")

    labelled = read([
        {"Period": "P01", "Cumulative planned value": 1_020_000},
        {"Period": "P02", "Cumulative planned value": 1_500_000},
    ])
    check([r["period_index"] for r in labelled] == [1.0, 2.0],
          "a period printed as 'P01' states index 1")

    section("5. WHAT IS NOT A TABLE YIELDS NOTHING")

    for bad in (None, "", 0, {}, "a paragraph of prose", [None, 3, "x"]):
        check(read(bad) == [], f"{bad!r} yields no rows")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — a crash must print a FAILING result line
        import traceback
        traceback.print_exc()
        check(False, f"suite crashed: {type(exc).__name__}: {exc}")
    finish()
