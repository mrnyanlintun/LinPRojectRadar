#!/usr/bin/env python3
"""
RUN 34 FINAL CLOSURE. THE PARAMETER-PROVENANCE COUNT GUARD.

WHAT WENT WRONG, AND IT WAS NEITHER NUMBER. The provenance artifact held 21 ROWS: 19 governed
parameters and 2 ACCEPTANCE COUNTERS. Nothing in the file distinguished them, so a row count and
a parameter count could not be told apart by any reader or any guard. Both figures ever published
were correct about different things -- 21 rows, 19 parameters -- and the apparent contradiction
came from reading one as the other.

THE FIX IS STRUCTURAL, NOT ARITHMETICAL. A declared `row_type` column, and every count taken over
`row_type == PARAMETER`. This suite asserts that structure holds and that the report's published
distribution agrees with the artifact, so the two can never drift apart again.

NOTHING HERE IS TAKEN ON TRUST FROM THE ARTIFACT UNDER TEST. The expected parameter set is derived
from the LIVE `canonical_v8` registry; the artifact is regenerated and compared byte for byte; and
the report's table is parsed out of the report itself.

Run (from server/):
    PYTHONIOENCODING=utf-8 python tests/test_run34_parameter_count_closure.py
"""

from __future__ import annotations

import csv
import os
import pathlib
import re
import subprocess
import sys
from collections import Counter

_HERE = pathlib.Path(__file__).resolve().parent
ROOT = _HERE.parents[1]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation import canonical_v8 as V8                          # noqa: E402

AUDIT = ROOT / "code_audit"
PROV = AUDIT / "run34_portfolio_parameter_provenance.csv"
CLOSURE = AUDIT / "run34_parameter_class_count_closure.csv"
REPORT = ROOT / "REPORT_2026-08-18_run34-portfolio-health-calibration.md"

PASS = TOTAL = 0
FAILURES: list[str] = []


def check(cond, name, detail=""):
    global PASS, TOTAL
    TOTAL += 1
    if cond:
        PASS += 1
        print(f"  PASS  {name}" + (f"  [{detail}]" if detail else ""))
    else:
        FAILURES.append(name)
        print(f"  FAIL  {name}  [{detail}]")
    return bool(cond)


def head(t):
    print("\n" + "=" * 94 + f"\n{t}\n" + "=" * 94)


def rows(path):
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


# =================================================================================================
head("1. THE ARTIFACTS ARE GENERATED, NOT HAND-AUTHORED")
# =================================================================================================
_before = {p.name: p.read_bytes() for p in (PROV, CLOSURE)}
_r = subprocess.run([sys.executable, str(ROOT / "server" / "tools" / "build_run34_artifacts.py")],
                    cwd=str(ROOT), capture_output=True, text=True,
                    env={**os.environ, "PYTHONIOENCODING": "utf-8"})
check(_r.returncode == 0, "the Run-34 artifact generator runs cleanly", _r.stderr[-200:])
for _n, _b in _before.items():
    check((AUDIT / _n).read_bytes() == _b,
          f"{_n} is byte-identical to what the generator produces")


# =================================================================================================
head("2. ROW TYPES: a row count and a parameter count are distinguishable")
# =================================================================================================
prov = rows(PROV)
check("row_type" in (prov[0] if prov else {}),
      "the provenance artifact declares a row_type column, so a counter row cannot be mistaken "
      "for a parameter row")
params = [r for r in prov if r["row_type"] == "PARAMETER"]
counters = [r for r in prov if r["row_type"] == "ACCEPTANCE_COUNTER"]
check(len(prov) == len(params) + len(counters),
      "every row is either a PARAMETER or an ACCEPTANCE_COUNTER; there is no third kind",
      f"{len(prov)} = {len(params)} + {len(counters)}")
check(len(counters) == 2
      and {r["parameter"] for r in counters} == {"UNCLASSIFIED PARAMETERS",
                                                 "UNSUPPORTED PARAMETERS APPLIED"},
      "the two acceptance counters are exactly the two known ones, and they are NOT parameters",
      str(sorted(r["parameter"] for r in counters)))
check(all(r["module"] == "-" and r["parameter_class"] == "-" for r in counters),
      "and each carries module '-' and class '-', which is what they always carried")


# =================================================================================================
head("3. THE PARAMETER ROWS, AGAINST THE LIVE REGISTRY")
# =================================================================================================
reg = {(p["module"], p["parameter"]): p for p in V8.PH_PARAMETERS}
art = {(r["module"], r["parameter"]): r for r in params}
check(len(params) == len(V8.PH_PARAMETERS),
      "the artifact holds one row per live registry parameter",
      f"artifact {len(params)} vs registry {len(V8.PH_PARAMETERS)}")
check(set(reg) == set(art),
      "MISSING GOVERNED PARAMETER RECORDS = 0 and UNEXPLAINED EXTRA RECORDS = 0",
      f"missing {sorted(set(reg) - set(art))}; extra {sorted(set(art) - set(reg))}")
check(all(art[k]["parameter_class"] == reg[k]["parameter_class"] for k in reg),
      "and every recorded class is the class the live registry declares")

_ids = [f"{r['module']}::{r['parameter']}" for r in params]
check(len(set(_ids)) == len(_ids), "DUPLICATE PARAMETER ROWS = 0",
      str([k for k, n in Counter(_ids).items() if n > 1]))
check(all(r["parameter_class"].strip() and r["parameter_class"] != "-" for r in params),
      "BLANK CLASSIFICATIONS = 0")
_illegal = [r["parameter_class"] for r in params
            if r["parameter_class"] not in V8.PARAMETER_CLASSES]
check(not _illegal, "ILLEGAL CLASSIFICATION VALUES = 0", str(_illegal))

dist = {c: sum(1 for r in params if r["parameter_class"] == c) for c in V8.PARAMETER_CLASSES}
check(sum(dist.values()) == len(params),
      "CLASSIFICATION COUNTS SUM TO THE PARAMETER TOTAL (not to the artifact row count)",
      f"{sum(dist.values())} == {len(params)}")
check(len(dist) == 7, "all seven permitted classes are reported, including zeros", str(dist))
check(dist["EMPIRICAL_CALIBRATION"] == 0,
      "EMPIRICAL_CALIBRATION = 0: nothing is empirically calibrated")
check(dist["HEURISTIC"] == 0,
      "HEURISTIC = 0: the two non-parameter rows are NOT heuristics, they are counters")

# NOTHING UNSUPPORTED IS APPLIED -- the one condition the registry exists to make checkable.
check(not V8.unsupported_applied(),
      "no parameter classified UNSUPPORTED is applied operationally",
      str([p["parameter"] for p in V8.unsupported_applied()]))


# =================================================================================================
head("4. THE FIVE MODULES, EXPECTED VERSUS REPRESENTED")
# =================================================================================================
for mid in sorted(V8.RESULT_KEYS):
    expected = {p["parameter"] for p in V8.parameters_for(mid)}
    represented = {r["parameter"] for r in params if r["module"] == mid}
    check(expected == represented and expected,
          f"{mid}: expected {len(expected)}, represented {len(represented)}, missing 0, extra 0",
          f"missing {sorted(expected - represented)}; extra {sorted(represented - expected)}")
check({r["module"] for r in params} == set(V8.RESULT_KEYS),
      "all five Portfolio Health modules are represented", str(sorted({r["module"]
                                                                      for r in params})))


# =================================================================================================
head("5. THE CLOSURE ARTIFACT, AND THE DISCREPANCY IT MUST NOT HIDE")
# =================================================================================================
clo = rows(CLOSURE)
_rec = {r["parameter"]: r for r in clo if r["row_type"] == "RECONCILIATION"}
check(_rec["total rows in the provenance artifact"]["current_value"] == str(len(prov)),
      "the closure records the artifact's true ROW count", str(len(prov)))
check(_rec["PARAMETER rows"]["current_value"] == str(len(params)),
      "and the true PARAMETER count, separately", str(len(params)))
check(_rec["unique parameter identities"]["current_value"] == str(len(set(_ids))),
      "and the true count of unique parameter identities")
check(_rec["SECTION_1_TARGET_DISCREPANCY"]["result"] == "REPORTED_DISCREPANCY",
      "THE SECTION-1 TARGET OF 21 PARAMETER IDENTITIES IS REPORTED AS A DISCREPANCY, NOT PADDED "
      "TO: there are 19 governed parameters and reaching 21 would require inventing two")
_cc = {r["parameter"]: int(r["current_value"]) for r in clo if r["row_type"] == "CLASS_COUNT"}
check(_cc == dist, "the closure's class counts are the artifact's own", str(_cc))
_mods = [r for r in clo if r["row_type"] == "MODULE_RECONCILIATION"]
check(len(_mods) == 5 and all(r["result"] == "PASS" for r in _mods),
      "five module reconciliations, all PASS")
_adj = [r for r in clo if r["row_type"] == "ADJUDICATED_NON_PARAMETER"]
check(len(_adj) == 2 and all(r["result"] == "PASS" for r in _adj),
      "and the two numeric literals adjudicated NOT to be parameters are recorded with reasons, "
      "rather than silently dropped", str([r["parameter"][:40] for r in _adj]))


# =================================================================================================
head("6. THE REPORT'S PUBLISHED DISTRIBUTION AGREES WITH THE ARTIFACT")
# =================================================================================================
# THIS IS THE GUARD THE ORIGINAL DEFECT NEEDED. The report publishes a class table; if it ever
# drifts from the artifact, or if a class is dropped from it, this goes red.
def parse_report_counts(text: str) -> dict[str, list[int]]:
    """
    EVERY published count for each class, not the first one found.

    The report carries the class table twice -- once in the provenance section and once in the
    count correction. Parsing only the first occurrence would let the second drift unnoticed, and
    a guard that can be satisfied by one of two disagreeing tables is not a guard. Every
    occurrence must equal the artifact.
    """
    out: dict[str, list[int]] = {}
    for cls in V8.PARAMETER_CLASSES:
        out[cls] = [int(m) for m in re.findall(
            r"^\|\s*`" + re.escape(cls) + r"`\s*\|\s*\**(\d+)\**\s*\|", text, re.M)]
    return {c: v for c, v in out.items() if v}


def parse_report_distribution(text: str) -> dict[str, int]:
    """The single agreed count per class, or a deliberate mismatch marker if they disagree."""
    counts = parse_report_counts(text)
    return {c: (v[0] if len(set(v)) == 1 else -1) for c, v in counts.items()}


_text = REPORT.read_text(encoding="utf-8")
_rep = parse_report_distribution(_text)
check(set(_rep) == set(V8.PARAMETER_CLASSES),
      "the report publishes a count for ALL SEVEN classes, so none can be quietly omitted",
      str(sorted(set(V8.PARAMETER_CLASSES) - set(_rep))))
_occurrences = parse_report_counts(_text)
check(all(len(set(v)) == 1 for v in _occurrences.values()),
      "every class count published in the report agrees with every other occurrence of it, so a "
      "second table cannot drift from the first",
      str({c: v for c, v in _occurrences.items() if len(set(v)) != 1}))
check(_rep == dist,
      "AND THE REPORT'S DISTRIBUTION EQUALS THE ARTIFACT'S, class for class",
      f"report {_rep} vs artifact {dist}")
check(sum(_rep.values()) == len(params),
      "and it sums to the true parameter total", f"{sum(_rep.values())} == {len(params)}")
check("19 parameters" in _text,
      "the report states the true parameter count in words")
check("Parameter-provenance count correction" in _text,
      "and carries the count-correction section, so the correction is visible rather than a "
      "silent replacement")
check("21 rows" in _text and "2 counters = 21 rows" in _text,
      "which explains the 21 as a ROW count and reconciles it: 19 parameters + 2 counters")


# =================================================================================================
head("7. THE GUARD WOULD HAVE CAUGHT A REPORT/ARTIFACT DISAGREEMENT")
# =================================================================================================
# Non-vacuity, proved on real text rather than asserted: a report whose table drops a class, or
# whose counts are the row count rather than the parameter count, must fail the section-6 checks.
_dropped = re.sub(r"^\|\s*`HEURISTIC`\s*\|.*$", "", _text, flags=re.M)
check(set(parse_report_distribution(_dropped)) != set(V8.PARAMETER_CLASSES),
      "a report with a class dropped from its tables FAILS the all-seven-classes check")
_split = _text.replace("| `HEURISTIC` | 0 | — |", "| `HEURISTIC` | 3 | — |", 1)
check(any(len(set(v)) != 1 for v in parse_report_counts(_split).values()),
      "and a report whose two tables DISAGREE fails the every-occurrence check, so the second "
      "table cannot mask a drift in the first")
_padded = _text.replace("| `UNSUPPORTED` | 7 |", "| `UNSUPPORTED` | 9 |", 1)
check(parse_report_distribution(_padded) != dist,
      "and a report padded to make the classes sum to 21 FAILS the equality check",
      "UNSUPPORTED 7 -> 9 would sum to 21 and is refused")


# =================================================================================================
head("8. WAS THERE EVER A REPORT/ARTIFACT DISAGREEMENT? Read both out of the merged commit")
# =================================================================================================
# The contract's premise is that the Run-34 report claimed 21 parameter-provenance rows while its
# distribution summed to 19. That is checked HERE, against the merged objects rather than against
# the working tree, because a claim about what a report said is a claim about a specific commit.
MERGED = "41f01e82a7614fad5e281862065e98d3e079bf91"


def git_show(path, rev=MERGED):
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


_old_report = git_show("REPORT_2026-08-18_run34-portfolio-health-calibration.md")
_old_prov = git_show("code_audit/run34_portfolio_parameter_provenance.csv")
check(bool(_old_report) and bool(_old_prov),
      f"both objects are readable at the merged commit {MERGED[:7]}")

_old_rows = list(csv.DictReader(_old_prov.splitlines()))
_old_params = [r for r in _old_rows
               if r["parameter_class"] in V8.PARAMETER_CLASSES]
_old_counters = [r for r in _old_rows if r["parameter_class"] == "-"]
check(len(_old_rows) == 21 and len(_old_params) == 19 and len(_old_counters) == 2,
      "AT THE MERGED COMMIT the artifact held 21 rows: 19 parameters and 2 acceptance counters",
      f"{len(_old_rows)} = {len(_old_params)} + {len(_old_counters)}")
check({r["parameter"] for r in _old_counters}
      == {"UNCLASSIFIED PARAMETERS", "UNSUPPORTED PARAMETERS APPLIED"},
      "and the two non-parameter rows were the two acceptance counters, exactly as now")

_old_dist = {c: sum(1 for r in _old_params if r["parameter_class"] == c)
             for c in V8.PARAMETER_CLASSES}
_old_rep = parse_report_distribution(_old_report)
check(_old_dist == dist,
      "the artifact's class distribution at the merged commit is the SAME distribution as now: "
      "this closure changed structure and description, not any classification", str(_old_dist))
check(_old_rep == _old_dist,
      "AND THE REPORT'S DISTRIBUTION AT THAT COMMIT ALREADY EQUALLED THE ARTIFACT'S. There was "
      "NO report/artifact disagreement to catch: both were correct, about different things -- "
      "21 rows and 19 parameters", f"report {_old_rep} vs artifact {_old_dist}")
check("19 parameters" in _old_report,
      "the merged report stated 19 parameters in words, so it never claimed 21 parameters")
for _bad in ("rows = 21", "21 parameters", "= 21"):
    check(_bad not in _old_report,
          f"and the merged report contains no {_bad!r} claim")
check("row_type" not in _old_prov,
      "WHAT WAS ACTUALLY MISSING: the merged artifact had no row_type column, so nothing "
      "distinguished a counter row from a parameter row and a row count could not be told from "
      "a parameter count by any reader or any guard")

print()
print("=" * 94)
print(f"RESULT: {PASS}/{TOTAL} checks passed")
print("=" * 94)
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print("  -", f)
sys.exit(1 if FAILURES else 0)
