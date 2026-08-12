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
from app.simulation.models import SIMULATION_VERSION, VALIDATED  # noqa: E402

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
check("this run touched no participant-facing browser asset",
      not [d for d in diff_names if d.startswith("assets/")])
check("this run touched no page the participant is served",
      not [d for d in diff_names if d.endswith(".html") and not d.startswith("tests")])
check("this run changed only the analytical layer under the application",
      all(d.startswith("server/app/simulation/") for d in diff_names
          if d.startswith("server/app/")))

# ---------------------------------------------------------------- GATE 10: versioning
check("the analytical layer is stamped at Run 10's version",
      SIMULATION_VERSION == "sim-2026.08-v4")
history = (ROOT / "server" / "app" / "simulation" / "models.py").read_text(encoding="utf-8")
for old in ("sim-2026.08-v2", "sim-2026.08-v3"):
    check(f"the freeze record for {old} is preserved rather than overwritten", old in history)
check("the synthetic package version in use is the corrected one",
      (ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.3").is_dir())

for f in failures:
    print("FAILED:", f)
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
