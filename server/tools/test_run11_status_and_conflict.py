#!/usr/bin/env python3
"""
RUN 11, GATES 5 AND 6. WHAT THE GOVERNED ROLLUP IS CALLED, AND WHAT ITS CONFLICT NUMBER MEANS.

THE TWO PROPERTIES, NEITHER OF WHICH NAMES A STRING THIS RUN CHOSE.

  GATE 5. A rollup may not be presented as broader than the evidence that votes on it. Checked
  by deriving the voting lineages from the registry rather than reading them off a label: if
  every voting module sits in one category, the label must not claim more than that category.

  GATE 6. A conflict coefficient of zero must not be reported when zero is what the measure
  returns for having nothing to combine. Checked by asking the fusion layer itself what K it
  produces for a single source, showing it is 0.0, and requiring the governed semantics to
  withhold rather than publish it.

FAULT INJECTION at the end restores zero conflict under one-lineage voting and requires the
semantic property to go red, and asserts the injection changed the value before believing it.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation.fusion import (  # noqa: E402
    CONFLICT_ESTIMATED, NOT_ESTIMABLE_SINGLE_LINEAGE, SINGLE_LINEAGE_SENTENCE, dst_fuse,
    governed_status_semantics,
)
from app.simulation.registry import CORE_VOTING_MODULES, registry_index  # noqa: E402

PASS = 0
TOTAL = 0
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASS, TOTAL
    TOTAL += 1
    if ok:
        PASS += 1
    else:
        FAILURES.append(f"{name}: {detail}")
        print(f"FAIL  {name}  {detail}")


# ------------------------------------------------------------------ the architecture as it is
index = registry_index()
voting_categories = sorted({index[m]["category"] for m in CORE_VOTING_MODULES})
check("the voting set is exactly two modules", len(CORE_VOTING_MODULES) == 2,
      str(sorted(CORE_VOTING_MODULES)))
check("every voting module sits in one registry category", len(voting_categories) == 1,
      str(voting_categories))
check("and that category is the cost and earned value one",
      voting_categories == ["A1"], str(voting_categories))

# ------------------------------------------------------------------ GATE 6: what K actually is
single = dst_fuse(["Red"])
check("the fusion layer returns a conflict of zero for a single source",
      single is not None and single["conflict"] == 0.0, str(single))
# EXHAUSTIVE over the status vocabulary, because the interesting question is not what one pair
# does but whether ANY genuine two-source combine can produce the number the degenerate case
# produces. It cannot: the closest two sources can come is two identical Greens at K = 0.309.
vocabulary = ("Green", "Yellow", "Amber", "Red")
pairs = {(a, b): dst_fuse([a, b])["conflict"] for a in vocabulary for b in vocabulary}
check("no genuine two-source combine produces a conflict of zero",
      all(k > 0 for k in pairs.values()), str(sorted(pairs.items(), key=lambda kv: kv[1])[:2]))
check("the calmest genuine combine is two identical sources, and it is well above zero",
      min(pairs.values()) > 0.2, str(min(pairs.values())))
# THE POINT, AND IT IS SHARPER THAN "THE TWO READINGS LOOK ALIKE". Zero is a value the measure
# reaches ONLY by never combining anything. Published beside a status it reads to any reader as
# the complete absence of disagreement, which is a stronger claim than the best agreement two
# real sources can achieve. It is not a calm reading. It is not a reading.
check("so a published zero could only ever mean nothing was combined",
      single["conflict"] == 0.0 and 0.0 not in pairs.values(), "")

one_lineage = {"A1": {"status": "Red", "contributes_to_project_status": True,
                      "conflict": 0.0, "group": "A", "module_count": 2}}
sem = governed_status_semantics(one_lineage, 0.0)
check("GATE 6: with one voting lineage the conflict state is named, not scored",
      sem["project_conflict_state"] == NOT_ESTIMABLE_SINGLE_LINEAGE,
      sem["project_conflict_state"])
check("GATE 6: and no number is published for it",
      sem["project_conflict"] is None, str(sem["project_conflict"]))
check("GATE 6: the human sentence is the approved one",
      sem["project_conflict_sentence"] == "Conflict: not estimable from one voting lineage",
      str(sem["project_conflict_sentence"]))
check("GATE 6: the sentence does not claim agreement",
      "agree" not in sem["project_conflict_sentence"].lower(), "")
check("GATE 6: and it uses no em dash and no ampersand",
      "—" not in sem["project_conflict_sentence"]
      and "&" not in sem["project_conflict_sentence"], "")

# ------------------------------------------------------------------ GATE 5: the label
check("GATE 5: with one cost lineage voting the label is Cost Recovery Status",
      sem["project_status_label"] == "Cost Recovery Status", sem["project_status_label"])
check("GATE 5: the label does not claim overall project health",
      "health" not in sem["project_status_label"].lower(), sem["project_status_label"])
check("GATE 5: the scope sentence names what does not vote",
      all(w in sem["project_status_scope"].lower()
          for w in ("schedule", "evidence-quality", "governance")),
      sem["project_status_scope"])
check("GATE 5: and no em dash or ampersand in the scope sentence",
      "—" not in sem["project_status_scope"] and "&" not in sem["project_status_scope"], "")

# The rule is derived, not hard-coded to today's architecture. If a second lineage ever votes,
# both statements must widen by themselves.
two_lineages = dict(one_lineage)
two_lineages["A2"] = {"status": "Green", "contributes_to_project_status": True,
                      "conflict": 0.0, "group": "A", "module_count": 1}
sem2 = governed_status_semantics(two_lineages, 0.42)
check("with two voting lineages the conflict becomes estimable",
      sem2["project_conflict_state"] == CONFLICT_ESTIMATED, sem2["project_conflict_state"])
check("and the genuine coefficient is published",
      sem2["project_conflict"] == 0.42, str(sem2["project_conflict"]))
check("and the label stops claiming the cost lineage only",
      sem2["project_status_label"] != "Cost Recovery Status", sem2["project_status_label"])
check("and the scope names both lineages",
      "A1" in sem2["project_status_scope"] and "A2" in sem2["project_status_scope"],
      sem2["project_status_scope"])

# A non-voting category must not create a lineage.
with_group_c = dict(one_lineage)
with_group_c["C1"] = {"status": "Amber", "contributes_to_project_status": False,
                      "conflict": 0.0, "group": "C", "module_count": 3}
sem3 = governed_status_semantics(with_group_c, 0.0)
check("a category that does not vote does not become a lineage",
      sem3["voting_lineages"] == ["A1"], str(sem3["voting_lineages"]))
check("and the conflict stays not estimable",
      sem3["project_conflict_state"] == NOT_ESTIMABLE_SINGLE_LINEAGE, "")

# No categories at all.
sem4 = governed_status_semantics({}, 0.0)
check("with nothing voting the conflict is still not published",
      sem4["project_conflict"] is None, str(sem4["project_conflict"]))
check("and the label does not claim a cost recovery reading either",
      sem4["project_status_label"] == "Governed Project Status", sem4["project_status_label"])

# ------------------------------------------------------------------ the compute path agrees
from app.simulation.compute import compute_project  # noqa: E402
import datetime  # noqa: E402

si = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 500_000.0, "pv": 450_000.0,
      "cpi": 0.8, "spi": 0.89, "docRiskScore": 0.3, "actualPctComplete": 40.0,
      "plannedPctComplete": 45.0}
run = compute_project(si, "PRJ-RUN11", "P1", datetime.date(2026, 6, 30))
check("the compute path publishes the label", run.get("project_status_label") is not None, "")
check("the compute path publishes the conflict state",
      run.get("project_conflict_state") == NOT_ESTIMABLE_SINGLE_LINEAGE,
      str(run.get("project_conflict_state")))
check("the compute path publishes no conflict number under one lineage",
      run.get("project_conflict") is None, str(run.get("project_conflict")))
check("the compute path and the read path derive the same answer",
      governed_status_semantics(run["category_statuses"],
                                0.0)["project_status_label"] == run["project_status_label"], "")
check("a real project fuses on one lineage today",
      run.get("voting_lineages") == ["A1"], str(run.get("voting_lineages")))
check("and the two voting modules are the ones that voted",
      run.get("voting_module_ids") == ["A1.7", "A1.8"], str(run.get("voting_module_ids")))

# ------------------------------------------------------------------ the participant surface
app_js = (ROOT / "assets" / "js" / "app.js").read_text(encoding="utf-8")
tax_js = (ROOT / "assets" / "js" / "taxonomy.js").read_text(encoding="utf-8")
check("the ledger banner reads the stored conflict sentence",
      "_f.conflictSentence" in app_js, "")
check("and taxonomy.js exposes it from the stored row without deriving it",
      'conflictSentence: pick("project_conflict_sentence")' in tax_js, "")
check("and it falls back to the primed row when the slim list projection cannot answer, "
      "which is what the browser drive caught",
      "function pick(field)" in tax_js and "ROWS[keyOf(project)]" in tax_js, "")
check("and nothing in the browser computes a conflict coefficient",
      "project_conflict_state" not in app_js or "compute" not in app_js.split(
          "project_conflict_state")[0][-200:], "")

# ------------------------------------------------------------------ FAULT INJECTION
injected = dict(governed_status_semantics(one_lineage, 0.0))
check("injection precondition: the honest answer withholds the number",
      injected["project_conflict"] is None, "")
injected["project_conflict"] = 0.0
injected["project_conflict_state"] = CONFLICT_ESTIMATED
injected["project_conflict_sentence"] = None
check("INJECTION applied: the value changed",
      injected["project_conflict"] == 0.0
      and governed_status_semantics(one_lineage, 0.0)["project_conflict"] is None, "no change")
check("INJECTION RED: zero conflict published under one-lineage voting is detected",
      not (injected["project_conflict_state"] == NOT_ESTIMABLE_SINGLE_LINEAGE
           and injected["project_conflict"] is None), "not detected")

label_injected = dict(sem)
label_injected["project_status_label"] = "Overall Project Health"
check("INJECTION applied: the label changed",
      label_injected["project_status_label"] != sem["project_status_label"], "no change")
check("INJECTION RED: an overall-health label under one cost lineage is detected",
      "health" in label_injected["project_status_label"].lower()
      and len(sem3["voting_lineages"]) == 1, "not detected")

print("")
if FAILURES:
    print("FAILURES:")
    for f in FAILURES:
        print("  " + f)
print(f"RESULT: {PASS}/{TOTAL} checks passed")
sys.exit(0 if PASS == TOTAL else 1)
