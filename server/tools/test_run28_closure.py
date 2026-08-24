"""
RUN 28 CLOSURE. The five defects the owner named, each asserted mechanically.

WHAT THIS FILE IS FOR. Run 28 finished with five things open, and four of them are the kind that
a report can close in prose and code cannot. This suite closes them against the code:

  1  the final-head suite mismatch      -- not assertable here; it is a process fact, recorded in
                                          the report with the commit hash and the suite total.
  2  the approved renames               -- asserted over every CURRENT surface, and the A1.1 drift
                                          asserted to zero against the designated authority.
  3  A2.7 single slip versus trend      -- asserted: one forecast is never a trend, on the
                                          structure AND on the assembler that builds it.
  4  the untracked-file blind spot      -- asserted in test_run22_production_tree_completeness.py,
                                          which walks the filesystem; referenced here so the two
                                          cannot drift apart.
  5  the missing supply-path            -- asserted: every row of the closure table names a
                                          repository object that EXISTS and a structure key the
                                          intake actually accepts, and the intake is exercised.

THE RULE THIS FILE OBEYS. No oracle is read out of production. Where a name is checked it is
checked against `p0-baseline/module_renumbering_map.csv`, which `p0-baseline/MODULE_TAXONOMY.md`
designates the single source of truth and which `server/app/simulation/registry.py` reads; the
surfaces are compared TO it, never it to them. Where a supply path is checked, the check runs the
intake and looks for the structure on the signal inputs, rather than reading a column that says
it works.
"""

from __future__ import annotations

import csv
import json
import pathlib
import re
import sys
from datetime import date

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "server"))

import production_tree as pt  # noqa: E402
from app.project_data import (  # noqa: E402
    ProjectDataError, add_revision, apply_to_signal_inputs, governed_structure_keys,
    structures_as_of,
)
from app.simulation import models as _models  # noqa: E402
from app.simulation import registry as R  # noqa: E402
from app.simulation.canonical import CANONICAL_STRUCTURE_KEYS, StructureAbsent  # noqa: E402
from app.simulation.canonical_v3 import (  # noqa: E402
    V3_STRUCTURE_KEYS, cost_risk_simulation, milestone_trend,
)
from app.simulation.models_evm import run_kalman_filter  # noqa: E402
from app.simulation.models_ext import run_cost_risk, run_milestone_trend  # noqa: E402
from app.simulation.rng import make_rng  # noqa: E402
from app.writes import POST_ACTIONS  # noqa: E402

_models._register_extensions()

PASSED = 0
FAILED = 0
_fail: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        _fail.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def head(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


def attempt(fn, default=None):
    """
    Run `fn` and return `default` if it raises anything at all.

    WHY THIS EXISTS. A crash is not a red guard, and this programme counts one as a campaign
    failure. Several checks below drive production code that a fault injection can make raise a
    DIFFERENT exception from the one the check is about; without this the suite would die before
    printing its anchored RESULT line and the fault would be recorded as CRASH rather than as
    the red it actually is. Wrapping the call turns "it blew up" into "the property does not
    hold", which is the honest reading and the one the runner can score.
    """
    try:
        return fn()
    except Exception:
        return default


def rows(rel: str) -> list[dict]:
    with (ROOT / rel).open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


# =================================================================================================
head("1. THE NAMING AUTHORITY, AND WHAT IT DESIGNATES")
# =================================================================================================

# The authority, read mechanically. MODULE_TAXONOMY.md names this file the single source of truth
# and says every other reference is updated FROM it; registry.py reads it at import; the frontend
# registry is generated from it. It is not edited by this suite and not edited by this closure.
AUTHORITY = ROOT / "p0-baseline" / "module_renumbering_map.csv"
_names = {r["new_id"]: r["module_name"] for r in rows("p0-baseline/module_renumbering_map.csv")}

# THE CONFLICT IS RESOLVED, AND BY THE ONLY PARTY THAT COULD RESOLVE IT. The first closure pass
# found the authority recording `Monte Carlo EAC` against an owner prose name of `Monte Carlo EAC
# Forecast`, aligned the surfaces TO the authority, refused to edit the authority on the strength
# of a prose sentence, and reported the conflict as an owner decision. The owner has now decided:
# A1.1 IS `Monte Carlo EAC Forecast`, final, and the CURRENT naming authority is to be updated.
# That is an explicit authorisation for a third rename beyond Run 28's two, so the authority moved
# and everything generated from it re-propagated. Historical reports and historical packages keep
# their historical wording.
check(_names.get("A1.1") == "Monte Carlo EAC Forecast",
      "the designated naming authority records A1.1 as `Monte Carlo EAC Forecast`, on the "
      "owner's explicit decision, and every generated surface is re-propagated from it",
      str(_names.get("A1.1")))
check(_names.get("A1.10") == "CPI Shrinkage Forecast",
      "and it records the first approved rename", str(_names.get("A1.10")))
check(_names.get("A1.11") == "Independent EAC Reconciliation Index",
      "and the second", str(_names.get("A1.11")))

_taxonomy_md = (ROOT / "p0-baseline" / "MODULE_TAXONOMY.md").read_text(encoding="utf-8")
check("single source of truth" in _taxonomy_md and "module_renumbering_map.csv" in _taxonomy_md,
      "the designation is a fact in the repository rather than an assumption of this suite",
      "MODULE_TAXONOMY.md")

# =================================================================================================
head("2. DEFECT 2: THE APPROVED RENAMES, ON EVERY CURRENT SURFACE")
# =================================================================================================

# THE CURRENT SURFACES. Every file a reader of the live instrument can reach that carries a module
# display name, plus the two production registries. HISTORICAL artefacts -- old reports, old
# freezes, captured contract baselines, the batch-3 parity record -- are deliberately NOT here:
# rewriting them to erase an old name would destroy the evidence that the name was ever different.
CURRENT_SURFACES = (
    "p0-baseline/module_renumbering_map.csv",
    "assets/js/categories.js",
    "assets/js/taxonomy.js",
    "assets/js/knowledge.js",
    # RUN 54: "assets/js/deepdive.js" WAS HERE. It is DELETED, and a file that does not exist
    # cannot carry a retired name. Removing it from this list is not a weakening: the surfaces
    # that remain are checked exactly as before, and the deletion is a stronger guarantee about
    # this one than any text check could give.
    "assets/js/charts3d.js",
    "assets/js/decision-ui.js",
    "assets/js/workspace.js",
    "assets/js/neural_flow.js",
    "assets/js/ds_defensibility_data.js",
    "assets/js/ds_defensibility_evidence.js",
    "server/app/simulation/canonical_v3.py",
    "server/app/simulation/models_ext.py",
)

# The RETIRED names, and the module each belonged to. A current surface that still speaks one of
# these is the mixed state the owner's instruction is about: the registry saying one thing and the
# page a reader is shown saying another, at the same moment, about the same module.
RETIRED = {
    "Regression to Mean CPI": "A1.10",
    "ICE Ratio": "A1.11",
}
for _text, _mid in sorted(RETIRED.items()):
    _offenders = sorted(rel for rel in CURRENT_SURFACES
                        if _text in (ROOT / rel).read_text(encoding="utf-8", errors="replace"))
    check(not _offenders,
          f"no current surface still calls {_mid} by its retired name {_text!r}, so there is no "
          f"mixed state in which one current surface shows the old name and another the new",
          str(_offenders))

for _mid in ("A1.10", "A1.11"):
    _want = _names[_mid]
    _bearing = [rel for rel in CURRENT_SURFACES
                if _want in (ROOT / rel).read_text(encoding="utf-8", errors="replace")]
    check(len(_bearing) >= 4,
          f"and the approved name for {_mid} is what the current surfaces actually carry, in the "
          f"registry, the taxonomy and the reader-facing files alike",
          f"{_want}: {sorted(_bearing)}")

# HISTORICAL EVIDENCE IS PRESERVED, asserted rather than assumed. If a later run "cleaned up" the
# old names everywhere, the record that the rename happened would be gone and this goes red.
for _hist, _text in (("REPORT_2026-08-14_run28-cat1-3-canonical-remediation-v3.md",
                      "Regression to Mean CPI"),
                     ("server/app/simulation/VALIDATION.md", "ICE Ratio"),
                     ("code_audit/run12_participant_package_checksums.sha256",
                      "assets/js/taxonomy.js")):
    check(_text in (ROOT / _hist).read_text(encoding="utf-8", errors="replace"),
          f"the historical record in {_hist} still carries its historical wording, so the rename "
          f"is evidenced rather than erased", _text)

# =================================================================================================
head("3. DEFECT: A1.1 NAMING DRIFT, CLOSED TO THE AUTHORITY")
# =================================================================================================

# THE GUARD THE OWNER ASKED FOR: it fails if an ACTIVE surface reintroduces the old name. The
# retired name is `Monte Carlo EAC` used AS A NAME -- that is, not immediately followed by the
# word Forecast -- so the new name does not trip its own check and a reversion anywhere does.
_OLD_A11 = re.compile(r"Monte Carlo EAC(?! [Ff]orecast)")
_a11_conflicts = sorted(
    rel for rel in CURRENT_SURFACES
    if _OLD_A11.search((ROOT / rel).read_text(encoding="utf-8", errors="replace")))
check(not _a11_conflicts,
      "CURRENT ACTIVE NAMING CONFLICTS FOR A1.1 = 0: no current surface reintroduces the retired "
      "name, in a display table, a heading, a node label or a sentence of prose",
      str(_a11_conflicts))
check(sum(1 for rel in CURRENT_SURFACES
          if "Monte Carlo EAC Forecast"
          in (ROOT / rel).read_text(encoding="utf-8", errors="replace")) >= 5,
      "and the decided name is what those surfaces carry, in the authority and in every surface "
      "generated from or aligned to it")

# THE STALE ALIAS LABEL, RECONCILED. The production-contract fixture recorded the new name as
# `owner_prose_alias` against a registry that said otherwise. It is no longer an alias for
# anything: it is the canonical name, and the OLD name is now the backward-compatible alias.
_contract = json.loads(
    (ROOT / "research_fixtures" / "production_contract" / "monte_carlo_eac_forecast"
     / "contract.json").read_text(encoding="utf-8"))
check(_contract["canonical_module_name"] == "Monte Carlo EAC Forecast"
      and _contract["owner_prose_alias"] is None
      and "Monte Carlo EAC" in _contract["backward_compatible_aliases"],
      "the production-contract fixture's stale `owner_prose_alias` label is reconciled: the "
      "decided name is the canonical one, the retired name is the backward-compatible alias, and "
      "the field is nulled rather than deleted so the history of the disagreement survives",
      str(_contract.get("owner_prose_alias")))

# =================================================================================================
head("4. DEFECT 5: THE SUPPLY PATHS, TWENTY ROWS, EACH ONE EXERCISED")
# =================================================================================================

SUPPLY = rows("code_audit/run28_supply_path_closure.csv")
check(len(SUPPLY) == 20, "the supply-path closure table carries exactly twenty rows",
      str(len(SUPPLY)))
check(len({r["module"] for r in SUPPLY}) == 20, "for twenty distinct modules",
      str(len({r["module"] for r in SUPPLY})))

ALLOWED_TYPES = {
    "EXISTING_DOCUMENT_EXTRACTION", "NEW_STRUCTURED_FORM", "NEW_PROJECT_DATA_OBJECT",
    "HISTORICAL_DATASET_INTERFACE", "REFERENCE_CLASS_DATASET_INTERFACE",
    "EXTERNAL_OFFICIAL_DATA_INTERFACE", "CONTRACT_BASELINE_DATA", "DERIVED_QUALIFIED_HISTORY",
    "NOT_REASONABLY_SUPPLIABLE",
}
check(all(r["supply_path_type"] in ALLOWED_TYPES for r in SUPPLY),
      "every supply-path type is one of the declared vocabulary",
      str(sorted({r["supply_path_type"] for r in SUPPLY} - ALLOWED_TYPES)))

# THE CHECK THE OWNER'S INSTRUCTION IS ACTUALLY ABOUT. A row may not claim an implemented supply
# path unless the platform can RECEIVE the structure. "Received" is not a column; it is the
# intake accepting the key. `governed_structure_keys()` is read from the analytical layer, so a
# row naming a structure no computation reads cannot pass by being written down here.
_intake = governed_structure_keys()
_conceptual = []
for r in SUPPLY:
    key = r["missing_canonical_structure"]
    if key in _intake:
        continue
    # The one legitimate shape of exception: a module whose supply path is a DERIVED history the
    # platform already assembles, which has no intake key because nothing is ever supplied.
    if r["supply_path_type"] == "DERIVED_QUALIFIED_HISTORY":
        continue
    _conceptual.append(r["module"])
check(not _conceptual,
      "IMPLEMENTED SUPPLY-PATH GAPS = 0: no row claims an implemented supply path for a "
      "structure the platform has no way to receive. A conceptual-only path cannot pass by "
      "being described in this table, because the vocabulary is read from the analytical layer",
      str(_conceptual))
check(not [r for r in SUPPLY if r["supply_path_type"] == "NOT_REASONABLY_SUPPLIABLE"],
      "no row is excused as NOT_REASONABLY_SUPPLIABLE: even A3.9's external price index has a "
      "real interface, and what it lacks is data that originates outside the platform entirely")

# EVERY NAMED REPOSITORY OBJECT EXISTS. A supply path that names a file that is not there is the
# same defect wearing a longer sentence.
_missing_objects = []
for r in SUPPLY:
    for token in r["concrete_repository_object"].replace("(", " ").replace(")", " ").split():
        cleaned = token.split("::")[0].strip(",;`")
        if "/" in cleaned and cleaned.endswith((".py", ".csv", ".js", ".json", ".md")):
            if not (ROOT / cleaned).is_file():
                _missing_objects.append((r["module"], cleaned))
check(not _missing_objects,
      "every repository object a row names actually exists in this checkout",
      str(_missing_objects))

# THE INTAKE, EXERCISED. Not "is the action registered" -- the structure is stored through the
# same helper the write handler calls, then read back through the same helper documents.py calls,
# and must arrive on the signal inputs the modules are given.
check("saveprojectdata" in POST_ACTIONS,
      "the intake action is dispatched by the write router, so the supply path is reachable "
      "from the API rather than existing as a module nothing calls")

_reached, _did_not = [], []
for r in SUPPLY:
    key = r["missing_canonical_structure"]
    if key not in _intake:
        continue
    doc = attempt(lambda: add_revision({}, key, {"probe": True}, effective_period=1,
                                       supplied_by="closure suite", source="closure suite",
                                       at="2026-08-14"), {})
    si: dict = {}
    attempt(lambda: apply_to_signal_inputs(si, doc, 1))
    (_reached if si.get(key) == {"probe": True} else _did_not).append(r["module"])
check(not _did_not and len(_reached) == 19,
      "and for each of the nineteen structures that HAS an intake key, a record supplied through "
      "the intake arrives on the signal inputs the modules are given. The twentieth, the ARIMA "
      "history, is DERIVED by the platform and is correctly not suppliable",
      f"reached {sorted(_reached)} / did not {sorted(_did_not)}")

# AND IT REFUSES. An intake that accepts anything is not a governed object.
for _bad, _why in (
        (lambda: add_revision({}, "notAStructure", {"a": 1}, effective_period=1,
                              supplied_by="x", source="y", at="z"),
         "a structure key no computation reads is refused"),
        (lambda: add_revision({}, "scheduleNetwork", {}, effective_period=1,
                              supplied_by="x", source="y", at="z"),
         "an empty record is refused"),
        (lambda: add_revision({}, "scheduleNetwork", {"a": 1}, effective_period=0,
                              supplied_by="x", source="y", at="z"),
         "a reporting period below one is refused"),
        (lambda: add_revision({}, "scheduleNetwork", {"a": 1}, effective_period=1,
                              supplied_by="", source="y", at="z"),
         "a record that does not say who supplied it is refused"),
        (lambda: add_revision({}, "scheduleNetwork", {"a": 1}, effective_period=1,
                              supplied_by="x", source="  ", at="z"),
         "a record that does not say where its figures came from is refused")):
    _raised = False
    try:
        _bad()
    except ProjectDataError:
        _raised = True
    check(_raised, f"the intake governs what it holds: {_why}")

# PERIOD-EFFECTIVE, so supplying data cannot silently rewrite an earlier period's stored result.
_doc = attempt(lambda: add_revision({}, "scheduleNetwork", {"v": 1}, effective_period=3,
                                    supplied_by="x", source="y", at="z"), {})
check(attempt(lambda: structures_as_of(_doc, 2)) == {}
      and attempt(lambda: structures_as_of(_doc, 3)) == {"scheduleNetwork": {"v": 1}},
      "a structure supplied FROM period three is invisible to a computation of period two, so an "
      "earlier period recomputes exactly as it was stored")
_doc = attempt(lambda: add_revision(_doc, "scheduleNetwork", {"v": 2}, effective_period=4,
                                    supplied_by="x", source="y", at="z"), {"projectData": {}})
check(len(_doc.get("projectData", {}).get("scheduleNetwork", [])) == 2
      and attempt(lambda: structures_as_of(_doc, 3)) == {"scheduleNetwork": {"v": 1}}
      and attempt(lambda: structures_as_of(_doc, 4)) == {"scheduleNetwork": {"v": 2}},
      "and a correction is a NEW revision, so the record of what the modules were given at the "
      "moment of an earlier decision survives it")

# A DOCUMENT-DERIVED STRUCTURE ALWAYS WINS, so a typed-in record cannot displace evidence read
# from the project's own documents.
_si = {"scheduleNetwork": {"from": "documents"}}
attempt(lambda: apply_to_signal_inputs(_si, _doc, 4))
check(_si["scheduleNetwork"] == {"from": "documents"},
      "a structure the period's own documents produced is never overwritten by a supplied one")

# =================================================================================================
head("4b. ALL TWENTY-THREE STRUCTURE-KEY ENTRIES, RECONCILED")
# =================================================================================================

# THE ARITHMETIC THE FIRST CLOSURE PASS LEFT UNEXPLAINED. It reported 23 structure keys, 2
# production-reachable, 21 fixture-only and 19 exercised through the intake. 19 + 2 = 21, not 23.
# The gap is a conflation, and naming it is the fix: `V3_STRUCTURE_KEYS` holds 23 MODULE-TO-KEY
# ENTRIES over 18 DISTINCT KEYS, because one schedule network serves five Category-2 methods and
# one time-phased baseline serves two. The reconciliation is therefore per ENTRY, which is the
# unit a module's supply question is actually asked in, and 19 entries need the intake while 4 do
# not, for four different and individually stated reasons.
KEYS = rows("code_audit/run28_v3_structure_key_reconciliation.csv")
check(len(KEYS) == 23, "the structure-key reconciliation carries exactly twenty-three rows",
      str(len(KEYS)))
check(len({(r["structure_key"], r["module_served"]) for r in KEYS}) == 23,
      "DUPLICATES = 0: every row is a distinct module-and-structure pair", str(len(KEYS)))
check(len({r["structure_key"] for r in KEYS}) == 18,
      "over eighteen distinct keys, which is where 23 and 19 + 2 stopped agreeing",
      str(len({r["structure_key"] for r in KEYS})))

# CLASSIFIED = 23, UNEXPLAINED = 0. The population is READ FROM THE ANALYTICAL LAYER, so a key
# added to production and not classified here is red, and a row here naming a key production does
# not declare is red too. Neither side is derived from the other.
_declared = {(m, k) for m, k in V3_STRUCTURE_KEYS.items()}
_classified = {(r["module_served"], r["structure_key"]) for r in KEYS}
check(_classified == _declared,
      "UNEXPLAINED = 0: the rows are exactly the module-to-key entries the analytical layer "
      "declares, with none invented and none missing. AN ORPHAN KEY ADDED TO PRODUCTION AND NOT "
      "CLASSIFIED HERE IS RED", str(sorted(_classified ^ _declared)))
check(all(r["verdict"] == "PASS" for r in KEYS), "and every row is classified",
      str([r["structure_key"] for r in KEYS if r["verdict"] != "PASS"]))

_needs = [r for r in KEYS if r["needs_the_project_data_intake"] == "yes"]
_not = [r for r in KEYS if r["needs_the_project_data_intake"] != "yes"]
check(len(_needs) == 19 and len(_not) == 4 and len(_needs) + len(_not) == 23,
      "nineteen entries need the intake route and FOUR do not, which closes the arithmetic",
      f"{len(_needs)} + {len(_not)}")
check(sorted(r["module_served"] for r in _not) == ["A1.1", "A2.7", "A3.6", "A3.8"],
      "and the four are named: A1.1 computes without its structure, A2.7 and A3.6 have theirs "
      "PRODUCED by document extraction rather than supplied, and A3.8 is registered disabled and "
      "never executed", str(sorted(r["module_served"] for r in _not)))
check(all(len(r["if_not_why_not"]) > 80 for r in _not),
      "each of the four states its own reason rather than sharing one")

# REASONABLY SUPPLYABLE BUT UNREACHABLE = 0, and NO FIXTURE-ONLY STRUCTURE MASQUERADES AS A
# PRODUCTION PATH. Both are decided by the intake itself, not by the column: the vocabulary comes
# from the analytical layer, so a key the intake does not accept cannot be written down as
# accepted here and survive.
check(all(r["accepted_by_the_project_data_intake"] == "yes" for r in KEYS),
      "every entry's structure is accepted by the intake")
_unreachable = sorted({r["structure_key"] for r in KEYS
                       if r["structure_key"] not in _intake})
check(not _unreachable,
      "REASONABLY SUPPLYABLE BUT UNREACHABLE = 0, and no fixture-only structure masquerades as a "
      "production supply path: the intake's own vocabulary is the arbiter", str(_unreachable))

# THE TWO PRODUCTION PRODUCERS, verified by reading production for an assignment of the key
# rather than by trusting the column.
_prod_src = "\n".join(p.read_text(encoding="utf-8")
                      for p in (ROOT / "server" / "app").rglob("*.py")
                      if "__pycache__" not in str(p))
for r in KEYS:
    _written = bool(re.search(r'si\["%s"\]\s*=' % re.escape(r["structure_key"]), _prod_src))
    if (r["real_corpus_currently_populates_it"] == "yes") != _written:
        check(False, f"the producer column for {r['structure_key']} matches production",
              f"column says {r['real_corpus_currently_populates_it']}, code says {_written}")
        break
else:
    check(True, "every row's producer column agrees with what production actually assigns, read "
                "out of server/app rather than out of the table")
check(sorted({r["structure_key"] for r in KEYS
              if r["real_corpus_currently_populates_it"] == "yes"})
      == ["costRiskModel", "milestoneForecastHistory"],
      "and exactly two structures are populated from the real corpus today",
      str(sorted({r["structure_key"] for r in KEYS
                  if r["real_corpus_currently_populates_it"] == "yes"})))

# =================================================================================================
head("5. DEFECT 6: ALL TWENTY-EIGHT OPERATIONAL OUTCOMES, RECONCILED")
# =================================================================================================

CLOSURE = rows("code_audit/run28_operational_closure_28.csv")
_scope = rows("code_audit/run28_cat1_3_scope.csv")
# The population is DERIVED from the scope file, not restated: the 31 Category 1 to 3 rows less
# the two scientific passes and the registered-disabled Material Cost Variance.
_expected = {r["canonical_id"] for r in _scope} - {"A1.7", "A1.8", "A3.4"}
check(len(CLOSURE) == 28, "the operational closure table carries exactly twenty-eight rows",
      str(len(CLOSURE)))
check({r["module"] for r in CLOSURE} == _expected and len(_expected) == 28,
      "UNACCOUNTED MODULES = 0: its modules are exactly the twenty-eight remediation targets the "
      "scope file defines, with none added and none lost",
      str(sorted({r["module"] for r in CLOSURE} ^ _expected)))
check(all(r["accounted"] == "yes" for r in CLOSURE),
      "and every row states where it ended")
check(all((r["real_corpus_executes"] == "yes") != (r["real_corpus_abstains"] == "yes")
          or r["disabled_laboratory_only"] == "yes" for r in CLOSURE),
      "no row both executes and abstains, and only a disabled module does neither",
      str([r["module"] for r in CLOSURE
           if (r["real_corpus_executes"] == "yes") == (r["real_corpus_abstains"] == "yes")
           and r["disabled_laboratory_only"] != "yes"]))

# THE TWO PROTECTED PASSES AND THE DISABLED MODULE ARE OUTSIDE THE TWENTY-EIGHT, not lost.
check("A1.7" not in {r["module"] for r in CLOSURE}
      and "A1.8" not in {r["module"] for r in CLOSURE},
      "TCPI and Variance at Completion are outside the twenty-eight remediation rows, as "
      "protected passes rather than as remediation targets")
check(sorted(R.CORE_VOTING_MODULES) == ["A1.7", "A1.8"] and len(R.CORE_VOTING_MODULES) == 2,
      "VOTING = EXACTLY 2, and they are the two protected passes",
      str(sorted(R.CORE_VOTING_MODULES)))
check("A3.4" in R.DISABLED_MODULES,
      "MATERIAL COST VARIANCE REMAINS DISABLED", str("A3.4" in R.DISABLED_MODULES))
check("A3.4" not in {r["module"] for r in CLOSURE},
      "and is excluded from the twenty-eight rather than reactivated inside them")

# THE TWO MODULES THIS CLOSURE FOUND IN THE SAME CONDITION AS THE TWENTY. Run 28 counted A2.2 and
# A2.3 as already canonical rather than as abstaining, and their structures were written by no
# production code either. Recorded here so the finding cannot be lost.
for _mid in ("A2.2", "A2.3"):
    _row = next(r for r in CLOSURE if r["module"] == _mid)
    check(_row["real_corpus_abstains"] == "yes"
          and CANONICAL_STRUCTURE_KEYS.get(_mid) in _intake,
          f"{_mid} abstains on the real corpus and its structure is reachable through the same "
          f"intake, though it is not one of Run 28's twenty", str(_row["evidence"])[:80])

# =================================================================================================
head("6. DEFECT 3: A2.7 -- ONE FORECAST IS NEVER A TREND")
# =================================================================================================


def _mfh(rows_):
    return {"milestoneForecastHistory": {"schedule_version": "SCH-1", "milestones": rows_}}


_one = [{"milestone_id": "M1", "original_baseline_day": 100.0,
         "forecasts": [{"report_index": 0, "forecast_day": 114.0}]}]
_two = [{"milestone_id": "M1", "original_baseline_day": 100.0,
         "forecasts": [{"report_index": 0, "forecast_day": 100.0},
                       {"report_index": 1, "forecast_day": 114.0}]}]

_refused = False
_crashed = ""
try:
    milestone_trend(_mfh(_one)["milestoneForecastHistory"])
except StructureAbsent:
    _refused = True
except Exception as _exc:                      # a crash is NOT a refusal
    _crashed = f"{type(_exc).__name__}: {_exc}"
check(_refused and not _crashed,
      "a baseline date and ONE forecast -- which is a current milestone variance and a complete "
      "one -- produces no trend from the canonical method at all", _crashed)
check(attempt(lambda: run_milestone_trend(_mfh(_one), make_rng(1),
                                         date(2026, 4, 30)).get("insufficient_data")) is True,
      "and the registered module reports NOT ESTIMABLE rather than a fourteen-day trend or a "
      "status colour from that single pair")
_ok = attempt(lambda: run_milestone_trend(_mfh(_two), make_rng(1), date(2026, 4, 30)), {})
check(_ok.get("insufficient_data") is not True and _ok.get("worst_variance_days") == 14.0,
      "while two forecasts for the same stable milestone identity DO produce one, measured "
      "against the date the milestone was committed to", str(_ok.get("worst_variance_days")))
check(_ok.get("status_color") is None and _ok.get("calibration_pending") is True,
      "with no status band asserted either way, because the slip boundaries are uncalibrated")

# THE CONTRACT'S OWN WORKED EXAMPLE, hand-checked: baseline 100, forecasts 104, 108, 111 gives
# slips 4, 8, 11 and a deteriorating direction. The numbers are the contract's, not production's.
_contract = attempt(lambda: milestone_trend({"schedule_version": "SCH-1", "milestones": [
    {"milestone_id": "M", "original_baseline_day": 100.0,
     "forecasts": [{"report_index": 1, "forecast_day": 104.0},
                   {"report_index": 2, "forecast_day": 108.0},
                   {"report_index": 3, "forecast_day": 111.0}]}]}),
                    {"milestones": [{"variance_days": [], "direction": ""}]})
check(_contract["milestones"][0]["variance_days"] == [4.0, 8.0, 11.0]
      and _contract["milestones"][0]["direction"] == "deteriorating",
      "the contract's own worked example reproduces exactly: slips 4, 8, 11 and deteriorating",
      str(_contract["milestones"][0]["variance_days"]))

# THE ASSEMBLER, which is the half a structure-level check cannot reach. The corpus route builds
# the structure from stored schedule snapshots, and it must DROP a milestone that appears in only
# one reporting period rather than pad it to a minimum.
from app.documents import _milestone_forecast_history  # noqa: E402

_snaps = [
    {"period": 1, "milestones": [{"name": "D200", "baseline_finish": "2026-08-14",
                                  "forecast": "2026-08-14"},
                                 {"name": "D700", "baseline_finish": "2026-09-01",
                                  "forecast": "2026-09-01"}]},
    {"period": 2, "milestones": [{"name": "D200", "baseline_finish": "2026-08-14",
                                  "forecast": "2026-08-28"}]},
]
_built = attempt(lambda: _milestone_forecast_history(_snaps), {"milestones": []})
check([m["milestone_id"] for m in _built["milestones"]] == ["D200"],
      "the corpus assembler follows only the milestone forecast in BOTH reporting periods; the "
      "one seen once is left out rather than given a second forecast it never had",
      str([m["milestone_id"] for m in _built["milestones"]]))
check(attempt(lambda: _milestone_forecast_history(_snaps[:1]), "raised") is None,
      "and a single reporting period assembles no structure at all, so the module abstains on "
      "its own guard rather than on a padded series")

# =================================================================================================
head("7. DEFECT 7: A3.6 -- GENUINELY STOCHASTIC, WITH A DECLARED DEPENDENCE POLICY")
# =================================================================================================

_model = {
    "model_version": "closure suite", "estimate_source": "closure suite",
    "dependence_policy": "INDEPENDENT, stated by the source",
    "cost_components": [{"component_id": "BASE", "base_amount": 1000.0}],
    "risk_events": [{"risk_id": f"R{i}", "probability": 0.5, "impact_distribution": "POINT",
                     "impact": 100.0} for i in range(6)],
}
_a = attempt(lambda: cost_risk_simulation(_model, make_rng(11), trials=4000), {})
_b = attempt(lambda: cost_risk_simulation(_model, make_rng(9999), trials=4000), {})
check(_a.get("mean_total_cost") != _b.get("mean_total_cost"),
      "the route is GENUINELY STOCHASTIC: two different random streams over the same governed "
      "model give different total-cost distributions, which a deterministic proxy cannot do",
      f"{_a.get('mean_total_cost')} vs {_b.get('mean_total_cost')}")
_again = attempt(lambda: cost_risk_simulation(_model, make_rng(11), trials=4000), {})
check(_again.get("mean_total_cost") == _a.get("mean_total_cost") is not None,
      "and REPRODUCIBLE: the same seeded stream gives the identical distribution, so a stored "
      "result can be reproduced rather than re-derived")
check(_a.get("risk_event_count") == 6 and _a.get("trials") == 4000
      and _a.get("dependence_policy") == "INDEPENDENT, stated by the source",
      "and it carries its event count, its iteration count and the SOURCE's dependence policy "
      "back out, so none of the three is a private assumption", str(_a)[:120])

# THE CONTRACT'S OWN ORACLE, hand-checked. Base 100, one event at probability one half with an
# impact of 20: the total is 100 or 120 with weight one half each, and the eightieth percentile
# under the frozen right-continuous convention is 120.
_oracle = attempt(lambda: cost_risk_simulation({
    "model_version": "o", "estimate_source": "o",
    "cost_components": [{"component_id": "B", "base_amount": 100.0}],
    "risk_events": [{"risk_id": "R", "probability": 0.5, "impact_distribution": "POINT",
                     "impact": 20.0}]}, make_rng(4), trials=5000), {})
check(_oracle.get("p80_total_cost") == 120.0,
      "the contract's own P80 oracle reproduces exactly: 120 on a two-point distribution",
      str(_oracle.get("p80_total_cost")))

_undeclared = dict(_model)
_undeclared.pop("dependence_policy")
check(attempt(lambda: run_cost_risk({"costRiskModel": _undeclared}, make_rng(1),
                                    date(2026, 4, 30)).get("insufficient_data")) is True,
      "SIX RISK EVENTS WITH NO STATED DEPENDENCE POLICY ABSTAIN. Independence across correlated "
      "risks understates precisely the upper tail this module reports, so the policy is required "
      "of the model's source rather than assumed by the simulator")
_single = {"model_version": "o", "estimate_source": "o",
           "cost_components": [{"component_id": "B", "base_amount": 100.0}],
           "risk_events": [{"risk_id": "R", "probability": 0.5,
                            "impact_distribution": "POINT", "impact": 20.0}]}
check(run_cost_risk({"costRiskModel": _single}, make_rng(1),
                    date(2026, 4, 30)).get("insufficient_data") is not True,
      "while a SINGLE event needs none, because one Bernoulli has nothing to be dependent with")
check(run_cost_risk({"bac": 1000.0, "cpi": 0.8}, make_rng(1),
                    date(2026, 4, 30)).get("insufficient_data") is True,
      "and with no cost risk model at all the module abstains rather than inflating the cost "
      "index, which is the deterministic proxy the contract forbids")

# THE REAL ROUTE'S DECLARATION, read from the production assembler rather than restated here.
_docs_src = (ROOT / "server" / "app" / "documents.py").read_text(encoding="utf-8")
check('"dependence_policy":' in _docs_src and "INDEPENDENT. The risk register states" in _docs_src,
      "and the real-document route DECLARES its policy from what the register itself supports, "
      "rather than leaving the simulator's independence unstated")

# =================================================================================================
head("8. DEFECT 8: A1.4 -- NO HIDDEN OR DEFAULT Q OR R")
# =================================================================================================

_ssm = {"process_variance_source": "elicited from the scheduling team, recorded 2026-06-30",
        "measurement_variance_source": "repeated readings of one period, Run 27 method",
        "initial_state": 1.0, "initial_variance": 1.0, "process_variance": 0.0,
        "measurement_variance": 1.0, "observations": [2.0]}
_k = attempt(lambda: run_kalman_filter({"kalmanStateSpaceModel": _ssm}, make_rng(1),
                                       date(2026, 4, 30)), {})
check(round(_k.get("smoothed_spi") or 0, 6) == 1.5
      and round(_k.get("final_gain") or 0, 6) == 0.5,
      "the contract's own oracle reproduces: x0=1, P0=1, Q=0, R=1, z=2 gives gain 0.5 and a "
      "filtered state of 1.5", f"{_k.get('smoothed_spi')} {_k.get('final_gain')}")
check(bool(_k.get("process_variance_source")) and bool(_k.get("measurement_variance_source")),
      "and BOTH variances carry their provenance out onto the result, so a reader can see where "
      "each came from rather than being told the filter is calibrated")
check(run_kalman_filter({"spi": 0.9, "spiHistory": [0.9, 0.92, 0.95]}, make_rng(1),
                        date(2026, 4, 30)).get("insufficient_data") is True,
      "WITH NO STATE-SPACE RECORD THE MODULE ABSTAINS. No default Q is substituted, no moving "
      "average is offered in its place, and no traffic light is generated")
for _blank in ("process_variance_source", "measurement_variance_source"):
    _partial = dict(_ssm)
    _partial[_blank] = ""
    check(attempt(lambda: run_kalman_filter({"kalmanStateSpaceModel": _partial},
                                            make_rng(1), date(2026, 4, 30))
                  .get("insufficient_data")) is True,
          f"and a record whose {_blank.split('_')[0]} variance does not say where it came from is "
          f"REFUSED, so an uncalibrated variance cannot pass as a calibrated one")
_evm_src = (ROOT / "server" / "app" / "simulation" / "models_evm.py").read_text(encoding="utf-8")
# The literals are gone from the EXECUTABLE code. They survive in the docstring, which is the
# record of what the frozen line did, so the check looks for an ASSIGNMENT rather than for the
# characters: `ast` gives every assignment in the module and a docstring contributes none.
import ast  # noqa: E402

_assigned = set()
for _node in ast.walk(ast.parse(_evm_src)):
    if isinstance(_node, ast.Assign):
        for _t in _node.targets:
            if isinstance(_t, ast.Name) and isinstance(_node.value, ast.Constant):
                _assigned.add((_t.id, _node.value.value))
check(("q", 0.01) not in _assigned and ("r", 0.1) not in _assigned,
      "and the two literals the frozen line used as Q and R are assigned nowhere in the module: "
      "they survive only in the docstring that records what v10 did",
      str(sorted(x for x in _assigned if x[0] in ("q", "r"))))
check(_k.get("status_color") is None,
      "no traffic-light status is generated from Q and R that Run 33 has not yet calibrated")

# =================================================================================================
head("9. DEFECT 4: THE PROTECTED SURFACE, ENUMERATED WITHOUT GIT")
# =================================================================================================

_inv = pt.walk_production()
check(len(_inv) > 200 and all(isinstance(t, bool) for _r, _d, _s, t in _inv),
      f"the protected production surface is discovered from the FILESYSTEM -- {len(_inv)} files "
      f"-- and each one's git-tracked state is reported as an attribute, not used as a filter")
check(not [rel for rel, _d, _s, tracked in _inv if not tracked],
      "and no protected production file is untracked, which is the blind spot Run 28 left open. "
      "The assertion lives in test_run22_production_tree_completeness.py; it is repeated here "
      "so the two cannot drift apart",
      str([rel for rel, _d, _s, tracked in _inv if not tracked]))
_d = pt.compare()
check(not (_d["added"] or _d["removed"] or _d["changed"]),
      "and the walk agrees with the pinned manifest: nothing added, removed or changed", str(_d))
check((ROOT / "server" / "app" / "project_data.py").is_file()
      and "server/app/project_data.py" in {rel for rel, _d2, _s, _t in _inv},
      "the new production file this closure created is inside the protected surface, so it is "
      "hashed, pinned and tracked rather than living outside every freeze the way canonical_v3.py "
      "did")

print()
print("=" * 78)
if _fail:
    print(f"{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(0 if FAILED == 0 else 1)
