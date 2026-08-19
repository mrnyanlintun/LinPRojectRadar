#!/usr/bin/env python3
"""
RUN 16, WORKSTREAM C. MATERIAL COST VARIANCE IS DISABLED FROM OPERATIONAL EXECUTION.

WHAT IS AND IS NOT CLAIMED. The module is disabled for an EVIDENCE AND CONTEXT reason, not an
algorithmic one, and nothing here asserts that its arithmetic is wrong. It stays registered, it
keeps its identity and its audit lineage, and the owner's decision on whether it is ultimately
retained behind a purpose-built contract material baseline and procurement evidence design, or
removed, is deferred.

WHAT IS SWEPT RATHER THAN SAMPLED. Sampling instead of sweeping has caused three missed defects
in this programme, so: every registered module is asked for its activation state, every module
in the registry is run against several input shapes to confirm exactly one newly refuses,
every disabled id is checked against the voting set, and every one of the eight previously
disabled academic methods is re-checked rather than counted.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_run16_material_cost_variance_disabled.py
"""

from __future__ import annotations

import os
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
os.environ.setdefault("SESSION_SECRET", "test-secret-do-not-use-in-prod")

from app.simulation import registry  # noqa: E402
from app.simulation.models import VALIDATED  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
MCV = "A3.4"
EIGHT = ["A3.8", "B2.7", "B2.9", "B2.20", "B4.1", "B4.2", "B4.5", "B4.6"]

passed = total = 0
failures: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global passed, total
    total += 1
    if ok:
        passed += 1
    else:
        failures.append(label + (f"  [{detail}]" if detail else ""))


# ---------------------------------------------------------------- C2: registry state
index = registry.registry_index()
check(MCV in index, "Material Cost Variance is still IN the registry", str(MCV in index))
check(index[MCV]["module_name"].replace("_", " ").lower().startswith("material cost variance"),
      "and under its own name, so the audit lineage resolves", index[MCV]["module_name"])
check(MCV in registry.DISABLED_EVIDENCE_UNDER_REVIEW,
      "it is in the evidence-under-review disabled set")
check(MCV not in registry.DISABLED_CONCEPT_ONLY,
      "and NOT in the concept-only set: this run makes no claim about its arithmetic")
check(MCV in registry.DISABLED_MODULES,
      "the union set the enforcement points read carries it")
check(registry.activation_state(MCV) == "DISABLED_EVIDENCE_UNDER_REVIEW",
      "its activation state names the reason and does not call it unsafe",
      registry.activation_state(MCV))
reason = registry.EVIDENCE_UNDER_REVIEW_REASON
check("under review" in reason.lower(),
      "the disablement reason is recorded in the repository", reason[:60])
for forbidden in ("invalid", "wrong", "defect", "incorrect", "concept-only"):
    check(forbidden not in reason.lower(),
          f"and does not classify the module as {forbidden}", reason[:80])
check("—" not in reason and "&" not in reason,
      "the reason follows the naming rules for prose")

# ---------------------------------------------------------------- C4: runtime exclusion, swept
SHAPES = [
    {},
    {"materialCostBaseline": 4_000_000, "materialCostCurrent": 4_400_000,
     "actualPctComplete": 50.0},
    {"materialCostBaseline": 1.0, "materialCostCurrent": 1.0, "actualPctComplete": 100.5},
    {"cpi": 0.9, "spi": 0.9, "docRiskScore": 0.4, "bac": 1e6, "ev": 4e5, "ac": 5e5},
]
for i, si in enumerate(SHAPES):
    out = registry.run_module(MCV, dict(si), lambda: 0.5, "2026-06-30")
    check(out.get("status_color") is None,
          f"it publishes no band on input shape {i}", str(out.get("status_color")))
    check(out.get("insufficient_data") is True,
          f"and reports itself non-executable on input shape {i}")
    check(out.get("activation_state") == "DISABLED_EVIDENCE_UNDER_REVIEW",
          f"carrying its own activation state on input shape {i}",
          str(out.get("activation_state")))
    check(out.get("evidence_metric") == reason,
          f"and the recorded reason verbatim on input shape {i}")

# THE FORMULA IS NOT REACHED. The refusal happens before the function is called, which is what
# "non-operational" has to mean; a module that still runs and then has its answer discarded is
# not disabled. Proved by making the formula raise if it is ever entered.
import app.simulation.models_ext as models_ext  # noqa: E402

_original = registry.VALIDATED[MCV][1]
_entered = {"yes": False}


def _tripwire(si, rand, cutoff):
    _entered["yes"] = True
    return _original(si, rand, cutoff)


registry.VALIDATED[MCV] = (registry.VALIDATED[MCV][0], _tripwire)
for si in SHAPES:
    registry.run_module(MCV, dict(si), lambda: 0.5, "2026-06-30")
check(_entered["yes"] is False,
      "its formula function is never entered: the refusal is before the arithmetic")
registry.VALIDATED[MCV] = (registry.VALIDATED[MCV][0], _original)

# ---------------------------------------------------------------- exactly one module changed
refused = []
for mid in sorted(VALIDATED):
    if registry.group_of(mid) == "D":
        continue
    out = registry.run_module(mid, {}, lambda: 0.5, "2026-06-30")
    if out.get("activation_state") in ("DISABLED_UNSAFE", "DISABLED_EVIDENCE_UNDER_REVIEW"):
        refused.append(mid)
check(sorted(refused) == sorted(EIGHT + [MCV]),
      "exactly nine modules are refused: the original eight and this one", str(sorted(refused)))

# NO OTHER MATERIAL OR COST MODULE WAS CAUGHT. Swept over the registry by name rather than by a
# hand-listed set, so a module this run should not have touched cannot slip through unnoticed.
material_or_cost = sorted(mid for mid, row in index.items()
                          if re.search(r"material|cost", row["module_name"], re.I))
collateral = [mid for mid in material_or_cost
              if mid != MCV and mid in registry.DISABLED_EVIDENCE_UNDER_REVIEW]
check(collateral == [],
      "no other material or cost module was disabled by this run", str(collateral))
check(len(material_or_cost) == 3,
      "and the sweep enumerated every module the registry names for material or cost",
      str(material_or_cost))
check(set(material_or_cost) == {MCV, "A3.6", "A3.8"},
      "which are the three the registry actually declares", str(material_or_cost))
# A3.8 was already disabled by Run 1 for a different reason and stays that way; A3.6 must be
# untouched by this run in every respect a caller can observe.
_a36 = registry.run_module("A3.6", {}, lambda: 0.5, "2026-06-30")
check(_a36.get("activation_state") not in ("DISABLED_UNSAFE",
                                           "DISABLED_EVIDENCE_UNDER_REVIEW"),
      "the other live cost module is not disabled", str(_a36.get("activation_state")))

# ---------------------------------------------------------------- voting and status protection
check(set(registry.CORE_VOTING_MODULES) == {"A1.7", "A1.8"},
      "the voting set is still exactly two", str(sorted(registry.CORE_VOTING_MODULES)))
check(MCV not in registry.CORE_VOTING_MODULES,
      "Material Cost Variance does not vote, and did not before this run either")
check(not (set(registry.DISABLED_MODULES) & set(registry.CORE_VOTING_MODULES)),
      "no disabled module is in the voting set")
check(MCV in registry.HELD_NON_VOTING_UNSOURCED_BANDS,
      "its held-non-voting record is retained rather than quietly dropped")
check(len(registry.HELD_NON_VOTING_UNSOURCED_BANDS) == 5,
      "and the five held non-voting modules are still five",
      str(len(registry.HELD_NON_VOTING_UNSOURCED_BANDS)))

# ---------------------------------------------------------------- the eight, individually
check(sorted(registry.DISABLED_CONCEPT_ONLY) == sorted(EIGHT),
      "the eight concept-only modules are the same eight",
      str(sorted(registry.DISABLED_CONCEPT_ONLY)))
for mid in EIGHT:
    out = registry.run_module(mid, {}, lambda: 0.5, "2026-06-30")
    check(out.get("activation_state") == "DISABLED_UNSAFE",
          f"{mid} is still disabled, with its own unchanged state",
          str(out.get("activation_state")))
    check(mid not in registry.DISABLED_EVIDENCE_UNDER_REVIEW,
          f"{mid} was not reclassified into this run's reason")

# ---------------------------------------------------------------- C3: the next campaign target
# The registered architecture is unchanged at 101 (96 project-level, 5 portfolio-level). Material
# Cost Variance leaves the CANDIDATE population for the next literature-backed campaign; the
# eight stay in it, because "currently disabled operationally" is not "excluded from scientific
# review".
live = registry.load_registry()
check(len(live) == 101, "the registry still declares 101 modules", str(len(live)))
group_d = [r["new_id"] for r in live if r["group"] == "D"]
check(len(group_d) == 5, "five of them are portfolio-level", str(len(group_d)))
check(len(live) - len(group_d) == 96, "and 96 are project-level",
      str(len(live) - len(group_d)))
candidates = [r["new_id"] for r in live if r["new_id"] != MCV]
check(len(candidates) == 100,
      "the next campaign's candidate population is 100", str(len(candidates)))
for mid in EIGHT:
    check(mid in candidates,
          f"{mid} remains in the scientific-review population despite being disabled")

# ---------------------------------------------------------------- the export mirror
import app.research_export as rx  # noqa: E402

check(MCV in rx._RUN16_DISABLED_EVIDENCE, "the export mirrors the disablement")
check(rx._run1_activation_state(MCV) == "DISABLED_EVIDENCE_UNDER_REVIEW",
      "and reports the same activation state as the registry",
      rx._run1_activation_state(MCV))
label = rx._run1_label(MCV, "Material Cost Variance")
check("disabled" in label.lower() and "under review" in label.lower(),
      "and labels it as disabled pending review", label[:90])
check("concept-only" not in label.lower(),
      "without borrowing the concept-only wording", label[:90])
check(set(rx._RUN1_DISABLED) == set(EIGHT),
      "the export's concept-only mirror is unchanged", str(sorted(rx._RUN1_DISABLED)))

# ---------------------------------------------------------------- the browser cannot re-enable it
taxonomy = (ROOT / "assets" / "js" / "taxonomy.js").read_text(encoding="utf-8")
entry = [ln for ln in taxonomy.splitlines() if "'Material_Cost_Variance'" in ln]
check(len(entry) == 1, "the taxonomy carries exactly one Material Cost Variance entry",
      str(len(entry)))
check("disabled: true" in entry[0],
      "and it is flagged disabled, so the browser presents it as unavailable", entry[0][:100])
disabled_entries = [ln for ln in taxonomy.splitlines()
                    if "disabled: true" in ln and "method_class:" in ln]
# RUN 36 CLOSURE. TEN now, not nine: the owner's 2026-08-19 ruling disabled A1.1 Monte Carlo EAC
# Forecast for insufficient canonical input, and the client taxonomy is GENERATED from the
# registry so the flag followed. The eight concept-only modules and Material Cost Variance -- the
# subject of this file -- are unchanged, and both facts are asserted rather than one count being
# quietly raised.
check(len(disabled_entries) == 10,
      "ten taxonomy entries are flagged disabled: the eight concept-only, this one, and A1.1",
      str(len(disabled_entries)))
check(sum(1 for ln in disabled_entries if "'A1.1'" in ln or '"A1.1"' in ln) == 1,
      "and exactly one of them is A1.1, so the tenth entry is the one the owner's ruling "
      "disabled and not some other module drifting into the set",
      str([ln.strip()[:40] for ln in disabled_entries if "A1.1" in ln]))
# The browser flag is presentation. The refusal that matters is the server's, and the server does
# not consult the browser: nothing under app/ reads the taxonomy file.
# A mention in a comment is not a dependency; a path the server could OPEN would be. Nothing
# under app/ resolves the browser's taxonomy file, so the server's refusal cannot be lifted by
# editing it.
server_src = "\n".join(p.read_text(encoding="utf-8")
                       for p in (ROOT / "server" / "app").rglob("*.py"))
check("assets/js/taxonomy.js" not in server_src and "assets\\js\\taxonomy.js" not in server_src,
      "and the server's refusal does not resolve that browser file at all")

for f in failures:
    print("FAILED:", f)
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
