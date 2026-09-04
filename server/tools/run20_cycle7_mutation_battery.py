"""RUN 20 CYCLE 7 MUTATION BATTERY, B2.1 evidence combination and the absorption rule.

Each mutation edits a production file, reruns the named suites, and must be CAUGHT. A mutation
that changes bytes without changing behaviour is not a survivor to be counted as caught either:
the battery asserts the bytes actually moved, and any mutation the suites let through is printed
as a survivor.
"""

# ---------------------------------------------------------------------------------------------
# RUN 135C. RETIRED ARTEFACT. This script is kept for the record and is NOT executed.
#
# Ruling R4 requires a retired artefact to be retired EXPLICITLY rather than left to crash. Its
# subject is B2.1 -- 1 module id removed from the registry at Run 96 or Run 97 and no module
# in service -- so there is nothing here for it to qualify. Before this guard it died with
# exit 1
# which prints no RESULT line and reads, in a scan of fleet output, exactly like a clean run.
#
# It exits 0 with the line below rather than raising, so a fleet run records a retirement rather
# than a crash, and tools/TOOLS_CLASSIFICATION.csv excludes it from qualification coverage.
# Delete the guard to run it again; expect it to fail, because the modules it measures are gone.
import sys as _sys135c
print("RETIRED: run20_cycle7_mutation_battery.py measures B2.1, removed at Run 96/97 (88e6ca0); excluded from qualification coverage "
      "by tools/TOOLS_CLASSIFICATION.csv")
_sys135c.exit(0)
# ---------------------------------------------------------------------------------------------
import os
import subprocess
import sys

G = "app/simulation/models_gov.py"
L = "app/simulation/lineage.py"
orig = {p: open(p).read() for p in (G, L)}

SUITES = ["test_run20_b21_dst_lineage.py", "test_run20_primitive_lineage.py",
          "test_run20_lineage_model.py", "test_run20_voting_lineage.py",
          "test_run20_lineage_reproduction.py", "test_run20_lineage_declaration_truth.py"]

MUTS = [
    ("M1 combine every arm as if independent, which is the defect itself", G,
     """        sources.append(arm_masses[pick])""",
     """        for _m in members:
            sources.append(arm_masses[_m])"""),
    ("M2 absorb the bridge into the first body in order, the pre-cycle-7 rule", L,
     """        overlaps = [(len(prim[i] & prim[selected[slot]]), -slot)
                    for slot in range(len(selected)) if dep[i][selected[slot]]]""",
     """        overlaps = [(0, -slot)
                    for slot in range(len(selected)) if dep[i][selected[slot]]]"""),
    ("M3 take the LEAST adverse reading within a body instead of the most", G,
     """        worst = max(BAND_SEVERITY.get(_arm_band(arm_masses[i]), -1) for i in members)""",
     """        worst = min(BAND_SEVERITY.get(_arm_band(arm_masses[i]), -1) for i in members)"""),
    ("M4 fold the document arm into the earned-value body: FALSE SUPPRESSION", G,
     """    "B2.1.doc", source_fact_ids=("doc_risk_score",),
    lineage_group_ids=(DOCUMENT_BODY,),""",
     """    "B2.1.doc", source_fact_ids=("doc_risk_score", "ev"),
    lineage_group_ids=(DOCUMENT_BODY, EARNED_VALUE_BODY),"""),
    ("M5 declare the cost forecast arm independent of everything: FALSE REINFORCEMENT", G,
     """    "B2.1.mc", source_fact_ids=("ac", "doc_risk_score", "ev", "pv"),
    lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),
    evidence_relationship=CORRELATED,""",
     """    "B2.1.mc", source_fact_ids=("mc_only",),
    lineage_group_ids=(),
    evidence_relationship=INDEPENDENT,"""),
    ("M6 restore the vacuous mass an absent arm used to contribute", G,
     """        arm(ARM_LINEAGE_EVM, m)""",
     """        arm(ARM_LINEAGE_EVM, m)
    else:
        sources.append({"Green": 0.25, "Amber": 0.25, "Red": 0.25, "Unknown": 0.25})"""),
    ("M7 report the conflict coefficient as estimable whatever the body count", G,
     """    conflict_estimable = len(sources) >= 2""",
     """    conflict_estimable = True"""),
    ("M8 restore the budget to the cost forecast arm, which does not read it", G,
     """    "B2.1.mc", source_fact_ids=("ac", "doc_risk_score", "ev", "pv"),""",
     """    "B2.1.mc", source_fact_ids=("ac", "bac", "doc_risk_score", "ev", "pv"),"""),
    ("M9 break the within-body tie toward the LAST arm rather than the first", G,
     """        pick = next(i for i in members
                    if BAND_SEVERITY.get(_arm_band(arm_masses[i]), -1) == worst)""",
     """        pick = [i for i in members
                if BAND_SEVERITY.get(_arm_band(arm_masses[i]), -1) == worst][-1]"""),
    ("M10 read an arm's band off the wrong end of its mass", G,
     """        if mass.get(b, 0.0) >= mass.get(best, 0.0):""",
     """        if mass.get(b, 0.0) <= mass.get(best, 0.0):"""),
    ("M11 drop the trend arm's shared this-period facts, hiding a real dependence", G,
     """    "B2.1.cusum", source_fact_ids=("ev", "pv", "reporting_history"),""",
     """    "B2.1.cusum", source_fact_ids=("reporting_history",),"""),
    ("M12 make the index arm and the document arm one body: FALSE SUPPRESSION", G,
     """    "B2.1.evm", source_fact_ids=("ac", "ev", "pv"),
    lineage_group_ids=(EARNED_VALUE_BODY,),""",
     """    "B2.1.evm", source_fact_ids=("ac", "ev", "pv", "doc_risk_score"),
    lineage_group_ids=(EARNED_VALUE_BODY, DOCUMENT_BODY),"""),
]


def restore():
    for p, s in orig.items():
        open(p, "w").write(s)


survivors = []
for name, path, old, new in MUTS:
    restore()
    src = orig[path]
    if old not in src:
        print(f"  ANCHOR MISSING  {name}")
        survivors.append(name + " (anchor missing)")
        continue
    mutated = src.replace(old, new, 1)
    if mutated == src:
        print(f"  NO BYTES CHANGED  {name}")
        survivors.append(name + " (no bytes changed)")
        continue
    open(path, "w").write(mutated)
    caught_by = []
    for suite in SUITES:
        r = subprocess.run([sys.executable, suite], cwd="tools", capture_output=True,
                           text=True, env=dict(os.environ, PYTHONIOENCODING="utf-8"))
        line = [ln for ln in r.stdout.splitlines() if ln.startswith("RESULT:")]
        if r.returncode != 0 or not line or line[-1].split()[1].split("/")[0] != \
                line[-1].split()[1].split("/")[1]:
            caught_by.append(suite)
    if caught_by:
        print(f"  CAUGHT  {name}\n            by {', '.join(caught_by)}")
    else:
        print(f"  SURVIVED  {name}")
        survivors.append(name)

restore()
print(f"\n{len(MUTS)} mutations, {len(survivors)} survivors")
if survivors:
    for s in survivors:
        print("  SURVIVOR: " + s)
sys.exit(1 if survivors else 0)
