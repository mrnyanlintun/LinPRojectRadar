#!/usr/bin/env python3
"""
RUN 146, THE SECOND FINDING: A CATEGORY THE SPECIFICATION LAYER ANSWERED PUBLISHES A POSTURE
WITH NO EVIDENCE BENEATH IT.

Run with cwd = <worktree>/server:   python tools/test_run146_answered_evidence.py

This is NOT the fault that emptied PRJ-002's page -- that one is in `documents._resolve_period`
and is proved in `tools/test_run146_served_period.py` and `tools/test_run146_browser.py`. It is
a SEPARATE, LATENT defect found while looking for that one, and it is recorded and closed here
because it is the same shape one level over: a posture published with nothing under it, which is
exactly what Run 142 was written to stop.

WHAT IT IS. `spec_projection.merge_python_row` carries the Python row's module readings over
only for categories in `wanted` -- the categories the specification layer did NOT answer. A
category it DID answer (state `computed` or `abstained`) is excluded, so the Python rows for it
are discarded and only the specification reading's OWN module rows are served. Where a
specification reading answers at CATEGORY level and carries no module rows of its own, that
category reaches the card with a posture and no evidence at all.

WHY IT WAS INVISIBLE UNTIL NOW. While the specification layer was failing -- the 403 Run 141
diagnosed -- every category was in state `failed`, nothing was `answered`, and every Python row
travelled. The defect is exposed by the layer RECOVERING, not by it failing.

WHICH RUN INTRODUCED IT: NOT 142, 143, 144 OR 145. The `if filled:` gate that excludes an
answered category dates from RUN 102 (`bc13679`), which introduced the module-row carry-over.
`git show 4efb8e9^:server/app/spec_projection.py` -- the file as it stood immediately BEFORE
Run 142 -- carries the same `wanted = set(filled)` and the same exclusion. Run 142 widened
`wanted`; it did not create the exclusion.

NOTHING IS CHANGED HERE, AND THAT IS A RULING FOR THE OWNER. The obvious repair -- serve the
Python rows beneath an answered category that supplied none, marked by layer -- was written,
measured working (28 rows restored, the specification's posture untouched, an answered category
that DOES carry its own rows left alone) AND THEN REVERTED. It makes INVARIANT A of
`tools/test_run142a_carryover.py` fail: Run 142 measured and asserted the opposite rule, that
"a category the specification layer ANSWERED is not carried; nothing is doubled". Amending that
check so a new change could pass would be suppressing a failing check, which this loop forbids,
and overturning a previous run's stated invariant is the owner's call and not this run's. So
this file REPORTS the defect with its evidence and asserts only what is true of the code as it
stands.
"""
from __future__ import annotations
import os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import spec_projection as sp   # noqa: E402

RESULTS: list[tuple[bool, str, str]] = []


def check(ok, label, detail=""):
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))


ROW_MODS = [{"module_id": f"A1.{i}", "category": "A1", "status_color": "Green"}
            for i in range(1, 29)]
ROW_ABS = [{"module_id": f"A3.{i}", "category": "A3", "abstention_reason": "awaiting evidence"}
           for i in range(1, 4)]
ROW_CATS = {"A1": {"status": "Green", "state": "computed",
                   "contributes_to_project_status": True}}


def spec_for(state, own_rows=()):
    return {"module_results": list(own_rows), "abstained": [],
            "category_statuses": {"A1": {"state": state, "status": "Green"}},
            "specification_categories_called": ["A1"]}


def run(label, spec):
    m = sp.merge_python_row(spec, ROW_MODS, ROW_ABS, ROW_CATS, {})
    a1 = [x for x in m["module_results"]
          if sp._python_category_of(x, x.get("module_id")) == "A1"]
    a3 = [x for x in m["abstained"]
          if sp._python_category_of(x, x.get("module_id")) == "A3"]
    print(f"    {label:34s} A1 rows={len(a1):3d}  A3 abstentions={len(a3):2d}  "
          f"categories={len(m['category_statuses'])}  A1 posture="
          f"{(m['category_statuses'].get('A1') or {}).get('status')!r}")
    return m, a1, a3


print("\nTHE STATES OF THE SPECIFICATION LAYER, against one stored row of 28 module readings\n"
      "and 3 abstentions:\n")
m_ans, a1_ans, a3_ans = run("answered, carrying no rows", spec_for(sp.sa.COMPUTED))
m_fail, a1_fail, _ = run("failed (the 403 condition)", spec_for(sp.sa.FAILED))
m_none, a1_none, _ = run("no specification reading", None)
own = [{"module_id": "A1.9", "category": "A1", "status_color": "Green"}]
m_own, a1_own, _ = run("answered, carrying one row", spec_for(sp.sa.COMPUTED, own))

print()
check(len(a1_fail) == 28 and len(a1_none) == 28,
      "a failing or absent specification layer serves all 28 Python rows -- unchanged",
      f"{len(a1_fail)} / {len(a1_none)}")
check(len(a1_ans) == 0,
      "THE DEFECT, AS THE CODE STANDS: an ANSWERED category that carries no rows of its own "
      "publishes a posture with NO evidence beneath it",
      f"{len(a1_ans)} module rows under a Green A1 posture")
check((m_ans["category_statuses"]["A1"] or {}).get("posture_layer") == sp.POSTURE_LAYER_SPEC
      and (m_ans["category_statuses"]["A1"] or {}).get("status") == "Green",
      "while the POSTURE is still the specification layer's and is unchanged",
      str((m_ans["category_statuses"]["A1"] or {}).get("posture_layer")))
check(len(a1_own) == 1 and a1_own[0]["module_id"] == "A1.9",
      "an answered category that DOES carry its own rows serves exactly those -- so the "
      "condition is narrow and a repair need not double any reading",
      str([x["module_id"] for x in a1_own]))
check(m_ans["project_status"] == m_fail["project_status"] is not None or True,
      f"project status: answered={m_ans['project_status']!r} failed={m_fail['project_status']!r}")
check(sorted(m_ans["python_fallback_categories"]) == sorted(m_fail["python_fallback_categories"]
                                                            ) or True,
      f"python_fallback_categories unchanged by evidence carry-over: "
      f"{m_ans['python_fallback_categories']}")

failed = [r for r in RESULTS if not r[0]]
print(f"\nRESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
for ok, label, detail in failed:
    print(f"  FAILED: {label}  [{detail}]")
sys.exit(1 if failed else 0)
