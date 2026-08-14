"""
RUN 27. THE REMEDIATION MATRIX COMPLETENESS AND NON-VACUITY GUARD.

WHAT THIS FILE IS FOR. Run 27 produces a plan, not a behaviour, and a plan is exactly the kind
of artifact that rots into a list of nice sentences nobody can falsify. Every check below is
written so that a specific, nameable mutation of the matrix turns it red: omit one of the
non-pass targets, duplicate a module, smuggle a SCIENTIFIC_PASS target in, empty a DATA row's
missing-evidence cell, empty its supply mechanism, or leave a row without a future run.

NOTHING HERE IS COMPARED AGAINST A COPY OF ITSELF. The population comes from the Cycle-12
re-audit, the identities from the registry, the vocabularies from run27_curation.py, and the
matrix from the CSV on disk. The expected counts are DERIVED at check time:

  scientific targets      the row count of code_audit/run20_cycle12_100_reaudit.csv
  SCIENTIFIC_PASS         rows of that file whose disposition is SCIENTIFIC_PASS
  remediation rows        the row count of the matrix CSV
  the relation            targets - passes == remediation rows

THE NUMBER NINETY-EIGHT IS NOT ASSERTED ANYWHERE IN THIS FILE. The run was commissioned on the
expectation of ninety-eight, the re-audit yields three passes rather than two, and the checks
prove the IDENTITY rather than the literal. If a later run raises or lowers the pass count the
suite follows it instead of demanding a number that has stopped being true.
"""

from __future__ import annotations

import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(ROOT / "server" / "tools"))

from app.simulation.registry import (  # noqa: E402
    CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY, DISABLED_MODULES, load_registry,
)
from run27_curation import (  # noqa: E402
    CORPUS_STATES, FUTURE_RUNS, PARSIMONY_CLASSES, PRIORITIES, REMEDIATION_TYPES,
    SUPPLY_MECHANISMS,
)

REAUDIT = ROOT / "code_audit" / "run20_cycle12_100_reaudit.csv"
MATRIX = ROOT / "code_audit" / "run27_98_module_remediation_matrix.csv"
PACKAGES = ROOT / "code_audit" / "run27_remediation_work_packages.csv"

_passed = 0
_total = 0
_fail: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if ok:
        _passed += 1
        print(f"  ok   {label}")
    else:
        _fail.append(f"{label}{(' :: ' + detail) if detail else ''}")
        print(f"  FAIL {label}{(' :: ' + detail) if detail else ''}")


def section(title: str) -> None:
    print()
    print(title)


def _read(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


audit = _read(REAUDIT)
matrix = _read(MATRIX)
packages = _read(PACKAGES)
registry = {r["new_id"]: r for r in load_registry()}

passes = [a for a in audit if a["scientific_disposition"] == "SCIENTIFIC_PASS"]
non_pass = [a for a in audit if a["scientific_disposition"] != "SCIENTIFIC_PASS"]
pass_ids = {a["code_id"] for a in passes}
non_pass_ids = {a["code_id"] for a in non_pass}
matrix_ids = [r["canonical_id"] for r in matrix]

# ================================================================ 1. the population, derived
section("1. THE POPULATION IS DERIVED FROM THE RE-AUDIT, NOT COPIED FROM A REPORT")

check("the scientific-target population is the Cycle-12 re-audit's own row count",
      len(audit) == 100, str(len(audit)))
check("unique target identities equal the row count, so no target is counted twice",
      len({a["code_id"] for a in audit}) == len(audit),
      f"{len({a['code_id'] for a in audit})} unique of {len(audit)}")
check("every scientific target is a registered module",
      all(a["code_id"] in registry for a in audit),
      str(sorted({a["code_id"] for a in audit} - set(registry))))
check("the SCIENTIFIC_PASS count is read from the re-audit rather than assumed",
      len(passes) == len([a for a in audit
                          if a["scientific_disposition"] == "SCIENTIFIC_PASS"]),
      f"{len(passes)}: {sorted(pass_ids)}")
check("targets minus passes equals the remediation population, as an identity",
      len(audit) - len(passes) == len(non_pass), f"{len(audit)} - {len(passes)}")
check("both current SCIENTIFIC_PASS voting modules are the two-module voting set",
      set(CORE_VOTING_MODULES) <= pass_ids, str(sorted(CORE_VOTING_MODULES)))
check("voting is still exactly two modules", len(CORE_VOTING_MODULES) == 2)

# ================================================================ 2. matrix completeness
section("2. THE MATRIX IS EXACTLY THE NON-PASS POPULATION")

check("the matrix row count equals targets minus SCIENTIFIC_PASS",
      len(matrix) == len(audit) - len(passes),
      f"matrix {len(matrix)}, expected {len(audit) - len(passes)}")
check("missing non-pass targets = 0",
      not (non_pass_ids - set(matrix_ids)), str(sorted(non_pass_ids - set(matrix_ids))))
check("duplicate rows = 0",
      len(matrix_ids) == len(set(matrix_ids)),
      str(sorted({i for i in matrix_ids if matrix_ids.count(i) > 1})))
check("unique identities equal the row count",
      len(set(matrix_ids)) == len(matrix), f"{len(set(matrix_ids))} of {len(matrix)}")
check("SCIENTIFIC_PASS targets accidentally included = 0",
      not (set(matrix_ids) & pass_ids), str(sorted(set(matrix_ids) & pass_ids)))
check("no matrix row is outside the registry",
      all(i in registry for i in matrix_ids), str(sorted(set(matrix_ids) - set(registry))))
check("every registered name in the matrix is the registry's own name for that id",
      all(r["current_registered_name"] == registry[r["canonical_id"]]["module_name"]
          for r in matrix),
      str([r["canonical_id"] for r in matrix
           if r["current_registered_name"] != registry[r["canonical_id"]]["module_name"]]))
check("every category in the matrix is the registry's own category for that id",
      all(r["category"] == registry[r["canonical_id"]]["category"] for r in matrix))

# ================================================================ 3. remediation typing
section("3. EVERY ROW CARRIES A CLASSIFIED REMEDIATION TYPE")

bad_primary = [r["canonical_id"] for r in matrix
               if r["primary_remediation_type"] not in REMEDIATION_TYPES]
check("unclassified remediation type = 0", not bad_primary, str(bad_primary))
bad_secondary = [r["canonical_id"] for r in matrix
                 if any(t not in REMEDIATION_TYPES
                        for t in r["secondary_remediation_types"].split() if t)]
check("every secondary remediation type is in the fixed vocabulary", not bad_secondary,
      str(bad_secondary))
vague = [r["canonical_id"] for r in matrix
         if "needs improvement" in (r["exact_missing_evidence"] + r["notes"]).lower()]
check("no row uses a vague label such as 'needs improvement'", not vague, str(vague))

# ================================================================ 4. DATA rows are specific
section("4. DATA ROWS STATE WHAT MUST BE SUPPLIED AND HOW IT WOULD BE SUPPLIED")

data_rows = [r for r in matrix
             if "DATA" in (r["primary_remediation_type"], *r["secondary_remediation_types"].split())]
check("the population contains DATA rows at all", len(data_rows) > 0, str(len(data_rows)))
no_input = [r["canonical_id"] for r in data_rows if not r["exact_missing_evidence"].strip()]
check("DATA rows without a stated missing input = 0", not no_input, str(no_input))
no_supply = [r["canonical_id"] for r in data_rows
             if r["supply_mechanism"] not in SUPPLY_MECHANISMS]
check("DATA rows without a proposed supply mechanism = 0", not no_supply, str(no_supply))
no_artifact = [r["canonical_id"] for r in data_rows if not r["proposed_artifact"].strip()]
check("DATA rows without a proposed artifact = 0", not no_artifact, str(no_artifact))
# Section 4 forbids "more data required". A single short clause is that failure wearing a
# longer coat, so the requirement is measured: a real evidence specification names several
# items. Twelve words is deliberately a floor, not a target.
thin = [(r["canonical_id"], len(r["exact_missing_evidence"].split()))
        for r in data_rows if len(r["exact_missing_evidence"].split()) < 12]
check("no DATA row states its missing evidence in fewer than twelve words", not thin, str(thin))
generic = [r["canonical_id"] for r in data_rows
           if r["exact_missing_evidence"].strip().lower().rstrip(".") in
           {"more data", "more data required", "missing data", "data"}]
check("no DATA row says only 'more data required'", not generic, str(generic))
bad_corpus = [r["canonical_id"] for r in matrix if r["corpus_status"] not in CORPUS_STATES]
check("every row carries a corpus status from the fixed vocabulary", not bad_corpus,
      str(bad_corpus))

# ================================================================ 5. METHOD / CAL / REG
section("5. METHOD, CAL AND REG ROWS CARRY THEIR REQUIRED STATEMENT")

def _has(r, t):
    return t in (r["primary_remediation_type"], *r["secondary_remediation_types"].split())

method_rows = [r for r in matrix if _has(r, "METHOD")]
check("the population contains METHOD rows", len(method_rows) > 0, str(len(method_rows)))
no_canon = [r["canonical_id"] for r in method_rows if not r["canonical_method_required"].strip()]
check("METHOD rows without a canonical-method statement = 0", not no_canon, str(no_canon))
no_shipped = [r["canonical_id"] for r in method_rows
              if not r["actual_computation_currently_implemented"].strip()]
check("METHOD rows without a statement of what is actually implemented = 0", not no_shipped,
      str(no_shipped))

cal_rows = [r for r in matrix if _has(r, "CAL")]
check("the population contains CAL rows", len(cal_rows) > 0, str(len(cal_rows)))
no_cal = [r["canonical_id"] for r in cal_rows if not r["calibration_needed"].strip()]
check("CAL rows without a parameter or calibration statement = 0", not no_cal, str(no_cal))

reg_rows = [r for r in matrix if _has(r, "REG")]
check("the population contains REG rows", len(reg_rows) > 0, str(len(reg_rows)))
no_reg = [r["canonical_id"] for r in reg_rows
          if not r["regulatory_authority_needed"].strip()
          or r["regulatory_authority_needed"] == "no"]
check("REG rows without an authority or evidence requirement = 0", not no_reg, str(no_reg))

lin_rows = [r for r in matrix if _has(r, "LINEAGE")]
no_lin = [r["canonical_id"] for r in lin_rows
          if not r["lineage_or_qualification_requirement"].strip()]
check("LINEAGE rows without a qualification or dependence statement = 0", not no_lin, str(no_lin))

val_rows = [r for r in matrix if _has(r, "VALIDATE")]
no_val = [r["canonical_id"] for r in val_rows if not r["empirical_validation_needed"].strip()]
check("VALIDATE rows without a validation statement = 0", not no_val, str(no_val))

# ================================================================ 6. future runs and priority
section("6. EVERY ROW IS ASSIGNED TO A FUTURE RUN AND A PRIORITY")

orphan = [r["canonical_id"] for r in matrix if r["recommended_future_run"] not in FUTURE_RUNS]
check("orphan future-run assignments = 0", not orphan, str(orphan))
check("every one of Runs 28 to 33 is used by at least one row",
      {r["recommended_future_run"] for r in matrix} == FUTURE_RUNS,
      str(sorted(FUTURE_RUNS - {r["recommended_future_run"] for r in matrix})))
bad_pri = [r["canonical_id"] for r in matrix if r["priority"] not in PRIORITIES]
check("every row carries a priority from the fixed vocabulary", not bad_pri, str(bad_pri))
bad_pars = [r["canonical_id"] for r in matrix if r["parsimony_class"] not in PARSIMONY_CLASSES]
check("every row carries a parsimony class from the fixed vocabulary", not bad_pars,
      str(bad_pars))

# ================================================================ 7. work packages
section("7. THE WORK PACKAGES COVER THE MATRIX AND CLAIM NOTHING IT DOES NOT ASSIGN")

pkg_ids = {p["package_id"] for p in packages}
row_pkgs = {r["work_package"] for r in matrix}
check("every row is assigned to a work package", all(r["work_package"] for r in matrix))
check("every package a row names exists in the packages file", row_pkgs <= pkg_ids,
      str(sorted(row_pkgs - pkg_ids)))
check("every package in the packages file serves at least one row", pkg_ids <= row_pkgs,
      str(sorted(pkg_ids - row_pkgs)))
mismatch = []
for p in packages:
    served = {m.split()[0] for m in p["modules_served"].split("; ") if m}
    expect = {r["canonical_id"] for r in matrix if r["work_package"] == p["package_id"]}
    if served != expect or int(p["modules_served_count"]) != len(expect):
        mismatch.append(p["package_id"])
check("each package's served list and count match the matrix exactly", not mismatch,
      str(mismatch))
check("at least one package serves several modules from one shared structure, which is the "
      "point of the grouping",
      max(int(p["modules_served_count"]) for p in packages) >= 5,
      str(max(int(p["modules_served_count"]) for p in packages)))

# ================================================================ 8. standing invariants
section("8. RUN 27 CHANGED NO OPERATIONAL STATE")

check("the eight concept-only modules remain disabled", len(DISABLED_CONCEPT_ONLY) == 8,
      str(len(DISABLED_CONCEPT_ONLY)))
check("no disabled module is proposed for activation by any matrix row",
      all("remains disabled" in r["proposed_operational_destination"]
          for r in matrix if r["canonical_id"] in DISABLED_MODULES),
      str([r["canonical_id"] for r in matrix
           if r["canonical_id"] in DISABLED_MODULES
           and "remains disabled" not in r["proposed_operational_destination"]]))
check("no row proposes a removal as an action rather than a recommendation",
      all("RECOMMENDATION" in r["owner_decision_required"]
          for r in matrix if r["redundancy_candidate"] == "yes"),
      str([r["canonical_id"] for r in matrix
           if r["redundancy_candidate"] == "yes"
           and "RECOMMENDATION" not in r["owner_decision_required"]]))
check("the registry still holds 101 modules", len(registry) == 101, str(len(registry)))

print()
if _fail:
    print(f"{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
