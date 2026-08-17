"""
Run 10, Gates 5 to 8 and 10. What this run must NOT have changed.

Every set here is derived from the repository rather than transcribed, so a drift shows up as a
failure rather than as a matching pair of edits.
"""
import csv
import hashlib
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("SESSION_SECRET", "test-secret-do-not-use-in-prod")

from app.simulation import registry  # noqa: E402
from app.simulation.models import (  # noqa: E402
    SIMULATION_VERSION, SIMULATION_VERSION_HISTORY, VALIDATED)

ROOT = pathlib.Path(__file__).resolve().parents[2]
passed = total = 0
failures = []


def check(name, cond):
    global passed, total
    total += 1
    if cond:
        passed += 1
    else:
        failures.append(name)


rows = list(csv.DictReader((ROOT / "code_audit" / "run8_module_classification.csv").open(encoding="utf-8")))
bucket = {b: sorted(r["module_id"] for r in rows if r["final_owner_action_bucket"] == b)
          for b in ("2", "3", "4", "5")}
for b, want in (("2", 16), ("3", 7), ("4", 2), ("5", 2)):
    check(f"bucket {b} holds exactly {want}", len(bucket[b]) == want)

# ---------------------------------------------------------------- GATE 5: Bucket 5 stays disabled
B5 = bucket["5"]
check("the two Bucket 5 modules are the ones Run 7 made abstain unconditionally",
      set(B5) == {"A3.1", "A5.1"})
for mid in B5:
    fn = VALIDATED[mid][1]
    for si in ({}, {"cpi": 0.9, "spi": 0.9, "bac": 1e6, "actualPctComplete": 40.0},
               {"referencePopulation": [1, 2, 3]}, {"dsm": {"nodes": 3}}):
        r = fn(dict(si), lambda: 0.5, "2025-06-30")
        check(f"{mid} abstains on {sorted(si)}", r.get("status_color") is None)
        check(f"{mid} publishes no band on {sorted(si)}",
              r.get("status_color") not in ("Green", "Yellow", "Amber", "Red"))
    check(f"{mid} is not in the voting set", mid not in registry.CORE_VOTING_MODULES)

# ---------------------------------------------------------------- GATE 6: voting does not expand
check("the voting set is exactly the two modules Run 4 left in it",
      set(registry.CORE_VOTING_MODULES) == {"A1.7", "A1.8"})
check("no module corrected by Run 10 joined the voting set",
      not (set(bucket["2"]) & set(registry.CORE_VOTING_MODULES)))
check("no Bucket 3 module joined the voting set",
      not (set(bucket["3"]) & set(registry.CORE_VOTING_MODULES)))
check("no Bucket 4 module joined the voting set",
      not (set(bucket["4"]) & set(registry.CORE_VOTING_MODULES)))
check("every voting module still carries a band source",
      set(registry.BAND_SOURCES) == set(registry.CORE_VOTING_MODULES))
check("the limit of what those citations establish is still stated",
      "not measured" in registry.BAND_SOURCE_LIMIT)
check("the five held non-voting modules are still held",
      set(registry.HELD_NON_VOTING_UNSOURCED_BANDS) ==
      {"A2.8", "A3.2", "A3.4", "A4.2", "A4.3"})
check("the eight concept-only modules are still disabled",
      len(registry.DISABLED_CONCEPT_ONLY) == 8)
check("no module Run 10 corrected was activated out of the disabled set",
      not (set(bucket["2"]) & set(registry.DISABLED_CONCEPT_ONLY)))

# ---------------------------------------------------------------- GATE 7: synthetic separation
SYN = ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.3" / \
    "Opus_Gubernatio_Synthetic_Programme_v0.3"
for name in ("module_id_aliases.csv", "module_asset_map.csv"):
    rs = list(csv.DictReader((SYN / name).open(encoding="utf-8")))
    check(f"{name} carries rows", len(rs) > 0)
    check(f"every row in {name} declares the research origin",
          all(r["data_origin"] == "SYNTHETIC_RESEARCH_FIXTURE" for r in rs))
    check(f"every row in {name} refuses empirical standing",
          all(str(r["not_for_empirical_validation"]).lower() == "true" for r in rs))
MC = ROOT / "research_fixtures" / "production_contract" / "monte_carlo_eac_forecast"
contract = json.loads((MC / "contract.json").read_text(encoding="utf-8"))
check("the forecast fixture family declares the research origin",
      contract["data_origin"] == "SYNTHETIC_RESEARCH_FIXTURE")
check("the forecast fixture family refuses empirical standing",
      contract["not_for_empirical_validation"] is True)
for row in csv.DictReader((MC / "known_answer_cases.csv").open(encoding="utf-8")):
    check(f"case {row['case_id']} declares the research origin",
          row["data_origin"] == "SYNTHETIC_RESEARCH_FIXTURE")
    check(f"case {row['case_id']} refuses empirical standing",
          row["not_for_empirical_validation"] == "true")
# No production module reads a synthetic fixture path.
prod_src = "\n".join(p.read_text(encoding="utf-8")
                     for p in (ROOT / "server" / "app").rglob("*.py"))
for needle in ("research_fixtures", "OG-SYNTH", "production_contract",
               "SYNTHETIC_RESEARCH_FIXTURE"):
    check(f"no production module under the application reaches for {needle}",
          needle not in prod_src)
check("no production module names a synthetic project identifier",
      "SYN-PRJ" not in prod_src)
# The synthetic tree is read-only to this run: nothing outside it was written into it.
check("the frozen v0.2 package is still present",
      (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.2").is_dir())
check("the frozen v0.3 package is still present", SYN.is_dir())
tri = json.loads((SYN / "package_A_project_structures" / "monte_carlo_contract.json")
                 .read_text(encoding="utf-8"))
check("the bottom-up triangular family is untouched and still triangular",
      tri["cost_element_distribution"]["type"] == "TRIANGULAR")
check("and still disclaims being the production oracle",
      "not_the_production_model" in tri)
check("the two families declare different distributions",
      tri["cost_element_distribution"]["type"] != contract["distribution"]["type"])

# ---------------------------------------------------------------- GATE 8: participant surface
PARTICIPANT_FILES = [
    ROOT / "server" / "app" / "research_decision.py",
    ROOT / "server" / "app" / "research_transitions.py",
    ROOT / "server" / "app" / "recommendation_basis.py",
]
diff_names = os.popen(f"cd {ROOT} && git diff --name-only origin/main").read().split()
for p in PARTICIPANT_FILES:
    rel = str(p.relative_to(ROOT))
    check(f"this run did not touch {rel}", rel not in diff_names)
# RESTATED BY RUN 11, ORIGINAL FINDING PRESERVED. Run 10 touched no browser asset and no served
# page, and that is still recorded as what Run 10 did. Run 11 Gate 1 is authorised to change the
# participant-route files that carried the dormant client arithmetic, and the researcher-side
# deep-dive page that now loads the algorithm version guard. The assertion keeps its force over
# everything else: the participant is still served no page this run altered, because the deep
# dive is not linked from the application and is not a participant surface.
RUN11_BROWSER_SCOPE = {
    "assets/js/client_algorithm_version.js",
    "assets/js/detail.js",
    "assets/js/signals.js",
    "assets/js/taxonomy.js",
    "assets/js/ds_defensibility_data.js",
    "assets/js/app.js",
    "assets/js/decision.js",
    "assets/js/ds_defensibility_evidence.js",
}
# index.html gains one script tag: the GENERATED defensibility evidence object, which the
# handbook on that page reads. It is a load, not a surface change of its own.
RUN11_PAGE_SCOPE = {"research/deepdive.html", "index.html"}
# RESTATED BY RUN 12, ORIGINAL FINDING PRESERVED. Run 11's list stands exactly as Run 11 left
# it. Run 12 adds ONE browser asset and names it here rather than widening the rule: the decision
# card, where driving the whole participant cycle in a real browser found that the preliminary
# judgment card was removed at the lock and never restored, so the second reporting period could
# not be started at all.
RUN12_BROWSER_SCOPE = {"assets/js/decision-ui.js"}
# RESTATED BY RUN 15, ORIGINAL FINDING PRESERVED. Run 15 adds ONE browser asset and names it
# rather than widening the rule: the methods knowledge base, whose entry for the portfolio
# anomaly module still described it as a distance proxy after that module became a real
# isolation forest. Leaving it would have had the client describe an algorithm the server no
# longer runs.
RUN15_BROWSER_SCOPE = {"assets/js/knowledge.js"}
# RESTATED BY RUN 16, ORIGINAL FINDING PRESERVED. Run 16 adds ONE browser asset and names it
# rather than widening the rule: the Signal Flow diagram, whose column headers reported the
# platform's registry counts as though they were the project's own activity, and whose every
# connection animated on a project with no evidence and no stored result. Both are presentation
# faults on a participant-visible surface and neither could be corrected anywhere else.
RUN16_BROWSER_SCOPE = {"assets/js/neural_flow.js"}
# RESTATED BY RUN 21, ORIGINAL FINDING PRESERVED. Run 21 adds ONE browser asset and names it
# rather than widening the rule: simulations.js, which computes fourteen models in the browser
# and went on publishing the four regulatory claims Run 20 cycle 2 withdrew from the SERVER --
# a FAR part number attached to an uncited overrun level, an OMB circular reduced to three
# thresholds and then said to make reporting mandatory, an EVM compliance said to be breached
# when no reporting cadence is held anywhere, and a constraint rule named after a regulation
# that states no such threshold. It is loaded by research/deepdive.html and tests.html and by NO
# participant route, so what it misled was the researcher on the deep-dive page. neural_flow.js
# is already named by Run 16 above and Run 21 corrects it again: after the supported reset it
# told the reader the project had no uploaded documents while the server still held them and was
# about to read them again. NO BAND, BOUNDARY, THRESHOLD OR ARITHMETIC RESULT CHANGED IN EITHER.
RUN21_BROWSER_SCOPE = {"assets/js/simulations.js", "assets/js/neural_flow.js"}
# RESTATED BY THE POST-RUN-22 UI CORRECTION, ORIGINAL FINDINGS PRESERVED. It adds TWO browser
# assets and names them rather than widening the rule. detail.js: the numbered Signal rail
# marked its chosen entry with `active`, the Signal Flow's own word for a category carrying
# current evidence, so a navigation SELECTION and an analytical ACTIVATION were the same state
# in the code; it published no aria-current; a click on a section already in view selected
# nothing; and the reset blanked the browser copy of the append-only event log, which made the
# live page deny retained documents that the SAME page, reloaded, correctly disclosed.
# radar.css: the rail sat at .7 opacity until hovered and was `display: none` below 700px, so
# on a phone every numbered control was unreachable. neural_flow.js is already named by Run 16
# and Run 21 above and this correction corrects it again: on an EMPTY project nine module dots
# and three document rows rendered at the ACTIVE opacity tier with a glow filter, because
# illumination was keyed on `status !== \'None\'` and a platform-disabled module is not None.
# NO BAND, BOUNDARY, THRESHOLD OR ARITHMETIC RESULT CHANGED IN ANY OF THEM.
RUN23_BROWSER_SCOPE = {"assets/js/detail.js", "assets/css/radar.css",
                       "assets/js/neural_flow.js"}
# RESTATED BY THE RUN-28 CLOSURE, ORIGINAL FINDINGS PRESERVED. It adds the browser assets that
# carry a MODULE NAME and names each of them rather than widening the rule. Run 28 renamed two
# Category-1 modules in the registry the owner designates as the source of truth and did NOT
# propagate the change, leaving the instrument in a mixed state: the registry said "CPI Shrinkage
# Forecast" and nine browser files still said "Regression to Mean CPI". The owner's closure
# instruction requires the current surface to be consistent. The same pass closes the A1.1 drift
# in the other direction, aligning the surfaces to the name the authority actually records.
# ONLY DISPLAY STRINGS CHANGED. No method class constant, no band, boundary, threshold or
# arithmetic result, and no step of the participant decision sequence.
RUN28_CLOSURE_BROWSER_SCOPE = {
    "assets/js/categories.js", "assets/js/taxonomy.js", "assets/js/knowledge.js",
    "assets/js/deepdive.js", "assets/js/charts3d.js", "assets/js/decision-ui.js",
    "assets/js/workspace.js", "assets/js/ds_defensibility_data.js",
    "assets/js/neural_flow.js", "assets/js/recommendation_options.js",
}
# RESTATED BY THE RUN-32 FINAL CLOSURE, ORIGINAL FINDING PRESERVED. Two further participant-
# facing assets move, and they are NAMED rather than the rule being widened to "assets/".
# `ds_defensibility_evidence.js` is the GENERATED defensibility object, regenerated because its
# generator was reading only four of the six canonical structure maps and therefore telling a
# reader that twenty-two modules required no governed structure while their production routes
# required one. `module_charts.js` keys a chart on B4.7's method class, which the section-3
# rename changed, so the chart had silently stopped being drawn.
#
# ONLY DISPLAY STRINGS AND A METHOD-CLASS KEY CHANGED. No band, boundary, threshold or
# arithmetic result, and no step of the participant decision sequence.
RUN32_CLOSURE_BROWSER_SCOPE = {
    "assets/js/ds_defensibility_evidence.js", "assets/js/module_charts.js",
}
check("this run touched no participant-facing browser asset outside Run 11's authorised scope",
      not [d for d in diff_names
           if d.startswith("assets/") and d not in RUN11_BROWSER_SCOPE
           and d not in RUN12_BROWSER_SCOPE and d not in RUN15_BROWSER_SCOPE
           and d not in RUN16_BROWSER_SCOPE and d not in RUN21_BROWSER_SCOPE
           and d not in RUN23_BROWSER_SCOPE and d not in RUN28_CLOSURE_BROWSER_SCOPE
           and d not in RUN32_CLOSURE_BROWSER_SCOPE])
check("this run touched no page the participant is served",
      not [d for d in diff_names if d.endswith(".html") and not d.startswith("tests")
           and d not in RUN11_PAGE_SCOPE])
# RESTATED BY RUN 11, ORIGINAL FINDING PRESERVED. Run 10 changed only the analytical layer, and
# that record stands. Run 11 Gate 6 additionally touches one file outside it: the read path that
# serves a stored result, which must derive the same conflict state the compute path derives or
# a stored row and a fresh response would disagree about whether the coefficient is estimable.
# It is named rather than admitted by widening the rule to "server/app/".
RUN11_NON_ANALYTICAL_SCOPE = {"server/app/documents.py"}
# RESTATED BY RUN 14, ORIGINAL FINDING PRESERVED. Run 14's subject is an input domain that no
# module owns: the fields whose own definition supplies an upper limit. The bound belongs with
# the field registry and the validator that enforces the numeric contract at every entry point,
# so those two files are named here rather than the rule being widened to "server/app/". No
# route, no model outside the simulation package, no storage behaviour and no participant
# surface is touched by this run.
RUN14_NON_ANALYTICAL_SCOPE = {"server/app/field_registry.py",
                              "server/app/extraction_merge.py"}
# RESTATED BY RUN 16, ORIGINAL FINDING PRESERVED. Run 16 touches two files outside the
# analytical layer and names them rather than widening the rule. The write path is where the
# clear-all workflow lives, and the defect this run fixed was that clearing a project's evidence
# left every result derived from it live and readable, which is a storage-lifecycle fault and
# cannot be corrected inside the simulation package. The export mirrors the registry's disabled
# sets by long-standing design, so a new disablement has to be mirrored there too.
RUN16_NON_ANALYTICAL_SCOPE = {"server/app/writes.py", "server/app/research_export.py"}
# RESTATED BY THE RUN-28 CLOSURE, ORIGINAL FINDINGS PRESERVED. It touches ONE further file
# outside the simulation package and names it rather than widening the rule to "server/app/".
# `project_data.py` is the intake path for the canonical structures Run 28's twenty abstaining
# modules are defined on: before it, twenty-one of the twenty-three v3 structure keys were
# written by no production code and appeared only in test fixtures, so the abstentions rested on
# a supply path that had been described and not built. It is a STORE, not a computation: it
# supplies no value, validates nothing for plausibility, and leaves every abstention exactly
# where canonical_v3's own guards put it. `writes.py` (the `saveprojectdata` action that reaches
# it) is already named by Run 16 above, and `documents.py` (the one merge point) by Run 11.
RUN28_CLOSURE_NON_ANALYTICAL_SCOPE = {"server/app/project_data.py"}
check("this run changed only the analytical layer under the application, plus the read path "
      "Run 11 Gate 6 names",
      all(d.startswith("server/app/simulation/") or d in RUN11_NON_ANALYTICAL_SCOPE
          or d in RUN14_NON_ANALYTICAL_SCOPE or d in RUN16_NON_ANALYTICAL_SCOPE
          or d in RUN28_CLOSURE_NON_ANALYTICAL_SCOPE
          for d in diff_names if d.startswith("server/app/")))

# ---------------------------------------------------------------- GATE 10: versioning
# RESTATED BY RUN 10B. The original assertion, that the layer is stamped sim-2026.08-v4, was
# correct for Run 10 and its record is kept here: Run 10 shipped sim-2026.08-v4. Run 10B changes
# what the layer emits again, so the stamp moves again and this check follows it, while the check
# below still proves every earlier stamp is preserved rather than overwritten.
check("the analytical layer is stamped at this run's version, and Run 10's sim-2026.08-v4 is "
      "kept as a historical audit baseline rather than being overwritten",
      SIMULATION_VERSION_HISTORY[-1] == SIMULATION_VERSION
      and "sim-2026.08-v4" in SIMULATION_VERSION_HISTORY)
history = (ROOT / "server" / "app" / "simulation" / "models.py").read_text(encoding="utf-8")
# RESTATED BY RUN 12, every earlier entry preserved: v5 and v6 join the list rather than
# replacing it, so each run's freeze record is asserted present for as long as the file exists.
for old in ("sim-2026.08-v2", "sim-2026.08-v3", "sim-2026.08-v4", "sim-2026.08-v5",
            "sim-2026.08-v6", "sim-2026.08-v9"):
    check(f"the freeze record for {old} is preserved rather than overwritten", old in history)
check("the synthetic package version in use is the corrected one",
      (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.3").is_dir())

for f in failures:
    print("FAILED:", f)
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
