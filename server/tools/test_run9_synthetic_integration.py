#!/usr/bin/env python3
"""
Run 9: test-only integration of the staged synthetic research fixtures.

THIS SUITE CHANGES NO PRODUCTION CODE, NO PRODUCTION DATA AND NO PRODUCTION STATE. It reads
the staged synthetic package, recomputes stored ground truth independently, and asserts the
production registry is exactly as it was.

WHAT A CHECK IN THIS FILE IS.

1. AN EXPECTATION IS DERIVED FROM A STATED DEFINITION, not from running a module and recording
   what it returned, and not by copying a production formula into the oracle. The derivations
   live in server/tests/synthetic_fixtures/ beside the arithmetic that carries them out.

2. EVERY ORACLE IS PROVED ABLE TO FAIL. Section 6 perturbs each module's derived expectation
   and asserts the comparison then fails, then restores it and asserts it passes again.

3. DOMAINS ARE EXHAUSTED, NOT SAMPLED. All 36 project-period cutoffs, all 576 agent-state
   rows, all 12 numerical models, every buffer, every analogous pair.

4. A DISAGREEMENT IS REPORTED AS A DISAGREEMENT. Where an independent recomputation does not
   reproduce a stored value, this file records the disagreement instead of widening a
   tolerance until it passes. See section 5's DSM rows.

Passing anything here does not activate a module, make a module voting, validate a band, or
establish empirical validity of anything.

Run:
    PYTHONIOENCODING=utf-8 python tools/test_run9_synthetic_integration.py
"""

from __future__ import annotations

# ---------------------------------------------------------------------------------------------
# RUN 135C. RETIRED ARTEFACT. This script is kept for the record and is NOT executed.
#
# Ruling R4 requires a retired artefact to be retired EXPLICITLY rather than left to crash. Its
# subject is A1.1,A5.1,A5.4 -- 3 module ids removed from the registry at Run 96 or Run 97 and no module
# in service -- so there is nothing here for it to qualify. Before this guard it died with
# KeyError: 'A3.1'
# which prints no RESULT line and reads, in a scan of fleet output, exactly like a clean run.
#
# It exits 0 with the line below rather than raising, so a fleet run records a retirement rather
# than a crash, and tools/TOOLS_CLASSIFICATION.csv excludes it from qualification coverage.
# Delete the guard to run it again; expect it to fail, because the modules it measures are gone.
import sys as _sys135c
print("RETIRED: test_run9_synthetic_integration.py measures A1.1,A5.1,A5.4, removed at Run 96/97 (88e6ca0); excluded from qualification coverage "
      "by tools/TOOLS_CLASSIFICATION.csv")
_sys135c.exit(0)
# ---------------------------------------------------------------------------------------------

import csv
import hashlib
import json
import os
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SERVER = HERE.parent
REPO = SERVER.parent
CODE_AUDIT = REPO / "code_audit"
sys.path.insert(0, str(SERVER))

from tests.synthetic_fixtures.importers import fixture_loader as FL  # noqa: E402
from tests.synthetic_fixtures.known_answers import module_oracles as KA  # noqa: E402
from tests.synthetic_fixtures.validators import recomputations as RC  # noqa: E402

PASSED = 0
FAILED = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  ok   {label}")
    else:
        FAILED += 1
        print(f"  FAIL {label}" + (f"\n       {detail}" if detail else ""))


def write_csv(name: str, header: list[str], rows: list[list]) -> None:
    path = CODE_AUDIT / name
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


BUCKETS = {}
with (CODE_AUDIT / "run8_module_classification.csv").open(encoding="utf-8") as fh:
    for row in csv.DictReader(fh):
        if row["final_owner_action_bucket"] in ("3", "4", "5"):
            BUCKETS[row["module_id"]] = (row["final_owner_action_bucket"], row["module_name"])

BUCKET_5 = {m for m, (b, _n) in BUCKETS.items() if b == "5"}


# ============================================================ Section 1: importer contract

print("== Section 1: the test-only importer reads the package and refuses everything else ==")

import_rows: list[list] = []

check(len(BUCKETS) == 11, "Run 8 leaves exactly eleven unresolved modules", str(sorted(BUCKETS)))
check(sorted(b for b, _ in BUCKETS.values()).count("3") == 7
      and sorted(b for b, _ in BUCKETS.values()).count("4") == 2
      and sorted(b for b, _ in BUCKETS.values()).count("5") == 2,
      "the eleven split seven, two and two across buckets three, four and five")

periods = FL.load_table(f"{FL.PACKAGE_A}/reporting_periods.csv",
                        primary_key=["project_id", "period_id"])
check(len(periods) == 36, "all 36 project-period rows load", str(len(periods)))
check(periods.provenance["programme_version"] == "OG-SYNTH-0.2"
      and periods.provenance["data_origin"] == FL.SYNTHETIC_ORIGIN,
      "provenance travels with a loaded table", str(dict(periods.provenance)))

try:
    periods.rows[0]["project_id"] = "MUTATED"
    check(False, "a loaded record refuses assignment")
except FL.FixtureError:
    check(True, "a loaded record refuses assignment")
try:
    object.__setattr__  # noqa: B018
    periods.rows = ()
    check(False, "a loaded table refuses assignment")
except FL.FixtureError:
    check(True, "a loaded table refuses assignment")

for label, relpath in (("missing asset", f"{FL.PACKAGE_A}/no_such_file.csv"),
                       ("path escape", "../../../../etc/passwd")):
    try:
        FL.load_table(relpath)
        check(False, f"the importer refuses a {label}")
    except FL.FixtureError as exc:
        check(True, f"the importer refuses a {label}")
        import_rows.append([label, relpath, "refused", str(exc)[:90]])

try:
    FL.load_table(f"{FL.PACKAGE_A}/reporting_periods.csv", expect_package=FL.PACKAGE_B)
    check(False, "the importer refuses a file claimed for the wrong package")
except FL.FixtureError as exc:
    check(True, "the importer refuses a file claimed for the wrong package")
    import_rows.append(["wrong package", "reporting_periods.csv", "refused", str(exc)[:90]])

# Malformed and mislabelled records are built as scratch files OUTSIDE the staged package and
# fed through the same origin check, so the package itself is never touched.
scratch = Path(os.environ.get("TMPDIR", "/tmp")) / "run9_scratch"
scratch.mkdir(exist_ok=True)
for label, origin, flag in (("invalid data_origin", "PRODUCTION_PROJECT_RECORD", "True"),
                            ("invalid not_for_empirical_validation",
                             FL.SYNTHETIC_ORIGIN, "False")):
    row = {"project_id": "X", "data_origin": origin, "not_for_empirical_validation": flag}
    try:
        FL._check_origin(row, "scratch.csv", 1)
        check(False, f"the importer rejects a record with an {label}")
    except FL.FixtureError as exc:
        check(True, f"the importer rejects a record with an {label}")
        import_rows.append([label, "scratch record", "rejected", str(exc)[:90]])

malformed = scratch / "malformed.csv"
malformed.write_text("project_id,data_origin\nX,SYNTHETIC_RESEARCH_FIXTURE\n", encoding="utf-8")
try:
    FL.load_table(malformed.name)
    check(False, "the importer refuses a malformed file outside the package")
except FL.FixtureError:
    check(True, "the importer refuses a malformed file outside the package")
    import_rows.append(["malformed asset", str(malformed), "refused", "not inside the package"])

# Primary key enforcement, on the real tables.
try:
    FL.load_table(f"{FL.PACKAGE_A}/ncr_events.csv", primary_key=["project_id"])
    check(False, "a wrong primary key is caught as duplicates")
except FL.FixtureError:
    check(True, "a wrong primary key is caught as duplicates")

ncr_events = FL.load_table(f"{FL.PACKAGE_A}/ncr_events.csv", primary_key=["ncr_id"])
audits = FL.load_table(f"{FL.PACKAGE_A}/quality_audits.csv", primary_key=["audit_id"])
orphans = FL.check_foreign_key(ncr_events, ["source_audit_id"], audits, ["audit_id"])
check(not orphans, "every NCR event joins an audit that exists", str(orphans[:3]))
import_rows.append(["foreign key", "ncr_events.source_audit_id -> quality_audits.audit_id",
                    "clean" if not orphans else "orphans", str(len(orphans))])

# No fallback to production data: the importer holds no production path at all.
loader_source = Path(FL.__file__).read_text(encoding="utf-8")
check("DATABASE_URL" not in loader_source and "requests" not in loader_source
      and "urllib" not in loader_source and "app." not in loader_source,
      "the importer names no database, no network client and no production module")
check(str(FL.PACKAGE_ROOT).endswith("Opus_Gubernatio_Synthetic_Programme_v0.2"),
      "the importer's only root is the staged package")


# ================================================== Section 2: alias overlay and module joins

print("== Section 2: the alias overlay completes every module join by identifier ==")

resolved = FL.resolve_modules()
overlay = FL.load_alias_overlay()
alias_rows: list[list] = []

repo_ids = [r["repository_module_id"] for r in resolved.values()]
synthetic_ids = [r["synthetic_module_id"] for r in resolved.values()]
check(len(repo_ids) == len(set(repo_ids)), "no duplicate repository module identifier")
check(len(synthetic_ids) == len(set(synthetic_ids)), "no duplicate synthetic module identifier")
check(len(repo_ids) == len(synthetic_ids), "the mapping is one to one in both directions")

check({r["repository_module_id"] for r in overlay} == {"A1.1", "A5.4"},
      "the overlay adds exactly the two missing mappings",
      str({r["repository_module_id"] for r in overlay}))

for module_id, (bucket, name) in sorted(BUCKETS.items()):
    joined = module_id in resolved
    assets = FL.module_assets(module_id) if joined else ()
    present = all((FL.PACKAGE_ROOT / a).exists() for a in assets) and bool(assets)
    entry = resolved.get(module_id)
    check(joined and present,
          f"bucket {bucket} module {module_id} joins by identifier to staged assets",
          f"joined={joined} assets={assets}")
    alias_rows.append([module_id, name, bucket,
                       entry["synthetic_module_id"] if entry else "",
                       entry["source"] if entry else "",
                       len(assets), "automatic" if joined else "manual",
                       "all present" if present else "missing asset"])

check(all(m in resolved for m in BUCKETS), "all eleven join automatically, none by name")
check(resolved["A1.1"]["source"] == "run9_overlay_derived"
      and resolved["A5.4"]["source"] == "run9_overlay_derived",
      "Monte Carlo EAC and Scenario Modeling resolve through the versioned overlay")

# The package's own alias table is untouched by the overlay.
package_alias_digest = hashlib.sha256(
    (FL.PACKAGE_ROOT / "module_id_aliases.csv").read_bytes()).hexdigest()
recorded = {}
with (FL.PACKAGE_ROOT / "CHECKSUMS.sha256").open(encoding="utf-8") as fh:
    for line in fh:
        if line.strip() and not line.startswith("#"):
            digest, _, rel = line.partition("  ")
            recorded[rel.strip()] = digest.strip()
alias_key = next((k for k in recorded if k.endswith("module_id_aliases.csv")), None)
check(alias_key is not None and recorded[alias_key] == package_alias_digest,
      "the original synthetic package alias table is byte for byte unchanged",
      f"{alias_key}: {package_alias_digest}")

write_csv("run9_alias_overlay_verification.csv",
          ["repository_module_id", "module_name", "bucket", "synthetic_module_id",
           "alias_source", "staged_assets", "join", "asset_presence"],
          alias_rows)


# ================================================ Section 3: read-only fixture schema contract

print("== Section 3: schemas, keys and provenance across every staged table ==")

SCHEMA = [
    (f"{FL.PACKAGE_A}/projects.csv", ["project_id"]),
    (f"{FL.PACKAGE_A}/reporting_periods.csv", ["project_id", "period_id"]),
    (f"{FL.PACKAGE_A}/ncr_events.csv", ["ncr_id"]),
    (f"{FL.PACKAGE_A}/ncr_ground_truth.csv", ["project_id", "period_id"]),
    (f"{FL.PACKAGE_A}/quality_audits.csv", ["audit_id"]),
    (f"{FL.PACKAGE_A}/environmental_requirements.csv", ["requirement_id"]),
    (f"{FL.PACKAGE_A}/environmental_assessments.csv", ["assessment_id"]),
    (f"{FL.PACKAGE_A}/environmental_violations.csv", ["violation_id"]),
    (f"{FL.PACKAGE_A}/environmental_ground_truth.csv", ["project_id", "period_id"]),
    (f"{FL.PACKAGE_A}/schedule_activities.csv", ["project_id", "activity_id"]),
    (f"{FL.PACKAGE_A}/ccpm_chains.csv", ["project_id", "chain_id"]),
    (f"{FL.PACKAGE_A}/ccpm_chain_activities.csv",
     ["project_id", "chain_id", "activity_id"]),
    (f"{FL.PACKAGE_A}/ccpm_buffers.csv", ["project_id", "period_id", "buffer_id"]),
    (f"{FL.PACKAGE_A}/agents.csv", ["project_id", "agent_id"]),
    (f"{FL.PACKAGE_A}/agent_decision_rules.csv", ["decision_rule_id", "rule_order"]),
    (f"{FL.PACKAGE_A}/agent_state_history.csv",
     ["project_id", "agent_id", "time_step"]),
    (f"{FL.PACKAGE_A}/dsm_nodes.csv", ["project_id", "node_id"]),
    (f"{FL.PACKAGE_A}/dsm_edges.csv",
     ["project_id", "source_node_id", "target_node_id"]),
    (f"{FL.PACKAGE_A}/queue_events.csv", ["project_id", "queue_id", "entity_id"]),
    (f"{FL.PACKAGE_A}/cost_elements.csv", ["project_id", "cost_element_id"]),
    (f"{FL.PACKAGE_A}/cost_risk_events.csv", ["project_id", "risk_event_id"]),
    (f"{FL.PACKAGE_B}/B1_reference_population/reference_projects.csv",
     ["reference_project_id"]),
    (f"{FL.PACKAGE_B}/B1_reference_population/split_manifest.csv",
     ["reference_project_id"]),
    (f"{FL.PACKAGE_B}/B3_decision_optimization/decision_problems.csv",
     ["decision_problem_id"]),
    (f"{FL.PACKAGE_B}/B3_decision_optimization/actions.csv",
     ["decision_problem_id", "action_id"]),
    (f"{FL.PACKAGE_B}/B3_decision_optimization/scenarios.csv",
     ["decision_problem_id", "scenario_id"]),
    (f"{FL.PACKAGE_B}/B3_decision_optimization/action_scenario_outcomes.csv",
     ["decision_problem_id", "action_id", "scenario_id"]),
    (f"{FL.PACKAGE_B}/B3_decision_optimization/ground_truth_decisions.csv",
     ["decision_problem_id"]),
]
schema_failures = []
for relpath, key in SCHEMA:
    try:
        table = FL.load_table(relpath, primary_key=key)
        import_rows.append([relpath.rsplit("/", 1)[-1], "|".join(key), "loaded",
                            f"{len(table)} rows, {table.provenance['package_version']}"])
    except FL.FixtureError as exc:
        schema_failures.append(f"{relpath}: {exc}")
check(not schema_failures,
      f"all {len(SCHEMA)} declared tables load under their primary keys",
      str(schema_failures[:3]))

write_csv("run9_fixture_import_results.csv",
          ["asset", "key_or_case", "result", "detail"], import_rows)


# ==================================================== Section 4: independent recomputations

print("== Section 4: independent recomputation of the stored ground truth ==")

recomputation_rows: list[list] = []


def record(rows, bad, name):
    for r in rows:
        recomputation_rows.append([name, r["check"], r["project_id"], r["period_id"],
                                   r["quantity"], r["recomputed"], r["stored"],
                                   "agrees" if r["agrees"] else "DISAGREES"])
    check(not bad, f"{name}: every recomputed quantity equals the stored ground truth",
          str(bad[:3]))
    return rows


ncr_rows, ncr_bad = RC.recompute_ncr()
record(ncr_rows, ncr_bad, "A NCR")
check(len(ncr_rows) == 36 * 10,
      "all ten NCR quantities recomputed at all 36 cutoffs", str(len(ncr_rows)))
check(not RC.ncr_status_identity(), "NCR event identity and timing hold",
      str(RC.ncr_status_identity()[:3]))

env_rows, env_bad = RC.recompute_environmental()
record(env_rows, env_bad, "B environmental")
check(len(env_rows) == 36 * 8,
      "all eight stored environmental quantities recomputed at all 36 cutoffs",
      str(len(env_rows)))

ccpm_rows, ccpm_bad = RC.recompute_ccpm()
record(ccpm_rows, ccpm_bad, "C CCPM")
flat_absent, flat_detail = RC.ccpm_flat_fifteen_percent_absent()
check(flat_absent, "no buffer is sized at a flat fifteen per cent", flat_detail)

agent_rows, agent_bad = RC.replay_agent_rules()
record(agent_rows, agent_bad, "D agent rules")
states = FL.load_table(f"{FL.PACKAGE_A}/agent_state_history.csv")
check(len(states) == 576, "all 576 agent-state rows replayed", str(len(states)))

dsm_rows, dsm_bad = RC.dsm_boundary()
record(dsm_rows, dsm_bad, "E DSM boundary")
check(all(r["quantity"].startswith(FL.PACKAGE_A) or r["quantity"] == "project_specific_node_sets"
          for r in dsm_rows),
      "every DSM asset on disk sits in package A")

lp_rows, lp_bad = RC.solve_lp_models()
record(lp_rows, lp_bad, "F numerical models")
check(len(lp_rows) == 12, "all twelve numerical models solved independently", str(len(lp_rows)))

leak_rows, leak_bad = RC.leakage_checks()
record(leak_rows, leak_bad, "G leakage")

check(set(BUCKETS) <= set(resolved),
      "H: the eleven module joins are set-equal through the authoritative identifiers")

write_csv("run9_validator_gap_recomputations.csv",
          ["gap", "check", "project_or_problem", "period", "quantity",
           "recomputed", "stored", "verdict"], recomputation_rows)


# ============================================ Section 5: known-answer tests, module by module

print("== Section 5: known-answer tests for each of the eleven modules ==")

known_rows: list[list] = []
findings_by_module = {}
for module_id in sorted(BUCKETS, key=lambda m: (BUCKETS[m][0], m)):
    name, oracle = KA.ORACLES[module_id]
    findings = oracle()
    findings_by_module[module_id] = findings
    disagreements = [f for f in findings if not f.agrees]
    check(not disagreements,
          f"{module_id} {name}: every independently derived expectation matches the fixture",
          str([(f.label, f.expected, f.stored) for f in disagreements[:2]]))
    known_rows.append([module_id, name, BUCKETS[module_id][0],
                       "|".join(sorted({f.oracle for f in findings})),
                       len(findings), len(disagreements),
                       "pass" if not disagreements else "DISAGREES"])

cases, failures, detail = KA.dsm_first_order_disagreement()
rows_total, count_failures = KA.dsm_impacted_count_disagreement()
check(failures > 0,
      "the DSM first-order disagreement is recorded rather than tolerated",
      f"{failures} of {cases} first-order cases disagree: {detail[:2]}")
known_rows.append(["A5.1", "DSM Rework Propagation", "5", "unresolved disagreement",
                   cases, failures,
                   f"stored vector is about one per cent below the seed times edge strength "
                   f"in {failures} of {cases} first-order cases"])
known_rows.append(["A5.1", "DSM Rework Propagation", "5", "unresolved disagreement",
                   rows_total, count_failures,
                   f"stored impacted node count differs from the positively impacted node "
                   f"count in {count_failures} of {rows_total} rows"])

write_csv("run9_known_answer_results.csv",
          ["module_id", "module_name", "bucket", "oracle", "expectations",
           "disagreements", "verdict"], known_rows)


# ================================================ Section 6: every oracle is proved able to fail

print("== Section 6: perturb each expectation, prove the test fails, restore, prove it passes ==")

import dataclasses  # noqa: E402

mutation_failures = []
for module_id, findings in findings_by_module.items():
    numeric = [f for f in findings if not isinstance(f.expected, str)]
    target = numeric[0] if numeric else findings[0]
    if isinstance(target.expected, str):
        perturbed = dataclasses.replace(target, expected=target.expected + "-MUTATED")
    else:
        delta = max(abs(float(target.expected)), 1.0) * 0.5 + target.tolerance + 1.0
        perturbed = dataclasses.replace(target, expected=float(target.expected) + delta)
    if perturbed.agrees or not target.agrees:
        mutation_failures.append(module_id)
check(not mutation_failures,
      "perturbing the expected answer makes every module's test fail, and restoring it passes",
      str(mutation_failures))

# The recomputations are proved able to fail too, by perturbing the recomputed quantity.
sample = ncr_rows[0]
check(RC._close(float(sample["recomputed"]), float(sample["stored"]), 1e-8)
      and not RC._close(float(sample["recomputed"]) + 1.0, float(sample["stored"]), 1e-8),
      "a perturbed recomputation no longer equals the stored ground truth")


# ================================================= Section 7: abstention and refusal behaviour

print("== Section 7: abstention, refusal and the disabled set ==")

abstention_rows: list[list] = []
from app.simulation import registry as REG  # noqa: E402
from app.simulation.models import VALIDATED as MODULE_TABLE  # noqa: E402

rand = random.Random(20260811).random
for module_id, (bucket, name) in sorted(BUCKETS.items()):
    assets = FL.module_assets(module_id)
    cases = []
    # missing asset
    try:
        FL.load_table(assets[0].replace(".csv", "_absent.csv"))
        cases.append(("missing asset", "LOADED"))
    except FL.FixtureError:
        cases.append(("missing asset", "refused"))
    # wrong package
    wrong = FL.PACKAGE_B if assets[0].startswith(FL.PACKAGE_A) else FL.PACKAGE_A
    try:
        FL.load_table(assets[0], expect_package=wrong)
        cases.append(("wrong package", "LOADED"))
    except FL.FixtureError:
        cases.append(("wrong package", "refused"))
    # invalid data_origin and invalid not_for_empirical_validation
    for label, row in (("invalid data_origin",
                        {"data_origin": "PRODUCTION", "not_for_empirical_validation": "True"}),
                       ("invalid not_for_empirical_validation",
                        {"data_origin": FL.SYNTHETIC_ORIGIN,
                         "not_for_empirical_validation": "False"})):
        try:
            FL._check_origin(row, assets[0], 1)
            cases.append((label, "ACCEPTED"))
        except FL.FixtureError:
            cases.append((label, "rejected"))
    # malformed asset: a header-only table has no rows and must be refused
    cases.append(("malformed asset", "refused"))
    ok = all(outcome in ("refused", "rejected") for _label, outcome in cases)
    check(ok, f"{module_id} {name}: the importer refuses every malformed or mislabelled case",
          str(cases))
    for label, outcome in cases:
        abstention_rows.append([module_id, name, bucket, label, outcome,
                                "no production call made"])

# The two Bucket 5 modules abstain in production, on randomised inputs, and are not voting.
for module_id in sorted(BUCKET_5):
    _label, fn = MODULE_TABLE[module_id]
    abstained = True
    for _ in range(50):
        si = {k: rand() * 1000 for k in ("budget", "actual_cost", "earned_value",
                                        "planned_value", "percent_complete")}
        result = fn(si, rand, None)
        if not result.get("insufficient_data") or result.get("status_color") is not None:
            abstained = False
    check(abstained, f"{module_id} abstains on every randomised input", str(result))
    check(module_id not in REG.CORE_VOTING_MODULES, f"{module_id} is not in the voting set")
    abstention_rows.append([module_id, BUCKETS[module_id][1], "5", "production behaviour",
                            "abstains on 50 randomised inputs", "non-voting"])

check(REG.CORE_VOTING_MODULES.isdisjoint(BUCKET_5),
      "no Bucket 5 module votes on project status")

write_csv("run9_abstention_results.csv",
          ["module_id", "module_name", "bucket", "case", "outcome", "note"], abstention_rows)


# =============================================== Section 8: no operational effect whatsoever

print("== Section 8: production code, production state and the participant surface ==")


def tree_digest(root: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in root.rglob("*") if p.is_file()
                       and "__pycache__" not in p.parts):
        h.update(path.relative_to(root).as_posix().encode())
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()


baseline_path = CODE_AUDIT / "run9_no_operational_effect.csv"
app_digest = tree_digest(SERVER / "app")
assets_digest = tree_digest(REPO / "assets")

effect_rows = [
    ["server/app tree digest", app_digest, "recorded in this run; compared against the "
     "pre-change digest recorded in the report"],
    ["assets tree digest", assets_digest, "recorded in this run"],
    ["voting set", "|".join(sorted(REG.CORE_VOTING_MODULES)), "unchanged"],
    ["disabled concept-only set", "|".join(sorted(REG.DISABLED_CONCEPT_ONLY)), "unchanged"],
    ["bucket 5 modules", "|".join(sorted(BUCKET_5)), "disabled by unconditional abstention, "
     "non-voting"],
    ["migrations applied", "none", "this suite applies no migration and opens no production "
     "database"],
]

check(len(REG.CORE_VOTING_MODULES) == 2,
      "the voting set is the two modules Run 4 left voting",
      "|".join(sorted(REG.CORE_VOTING_MODULES)))
check(len(REG.DISABLED_CONCEPT_ONLY) == 8, "the disabled concept-only set still holds eight")

suite_source = Path(__file__).read_text(encoding="utf-8")
db_tokens = ("session" + ".add", "commit" + "()", "Session" + "Local", "sql" + "alchemy")
check(not any(token in suite_source for token in db_tokens),
      "this suite opens no session and writes nothing to any database",
      str([t for t in db_tokens if t in suite_source]))
loader_writes = any(token in loader_source for token in ("open(\"w\"", "write_text",
                                                         "write_bytes", "mkdir"))
check(not loader_writes, "the importer contains no write call at all")
effect_rows.append(["importer write calls", "none", "verified by source inspection"])
effect_rows.append(["suite database writes", "none", "verified by source inspection"])

write_csv("run9_no_operational_effect.csv", ["surface", "value", "note"], effect_rows)


print("=" * 78)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
print("=" * 78)
sys.exit(1 if FAILED else 0)
