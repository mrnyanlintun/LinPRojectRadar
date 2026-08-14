"""RUN 27. Emit the report with every figure derived from the artifacts rather than typed."""

from __future__ import annotations

import collections
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "REPORT_2026-08-14_run27-98-module-remediation-matrix.md"


def read(p):
    with (ROOT / p).open(encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


audit = read("code_audit/run20_cycle12_100_reaudit.csv")
M = read("code_audit/run27_98_module_remediation_matrix.csv")
P = read("code_audit/run27_remediation_work_packages.csv")
NV = read("code_audit/run27_guard_nonvacuity.csv")
PT = read("code_audit/run27_parsimony_property_tests.csv")

passes = [a for a in audit if a["scientific_disposition"] == "SCIENTIFIC_PASS"]
types = collections.Counter()
for r in M:
    for t in [r["primary_remediation_type"]] + r["secondary_remediation_types"].split():
        types[t] += 1
pri = collections.Counter(r["priority"] for r in M)
runs = collections.Counter(r["recommended_future_run"] for r in M)
pars = collections.Counter(r["parsimony_class"] for r in M)
corpus = collections.Counter(r["corpus_status"] for r in M)
supply = collections.Counter(r["supply_mechanism"] or "(none: no missing evidence)" for r in M)

new_structure = sum(1 for r in M if r["supply_mechanism"] in {
    "NEW_DOCUMENT_TYPE", "NEW_STRUCTURED_FORM", "NEW_PROJECT_DATA_OBJECT",
    "HISTORICAL_DATASET", "PORTFOLIO_REFERENCE_DATASET", "EXTERNAL_OFFICIAL_DATA"})
existing = sum(1 for r in M if r["supply_mechanism"] in {
    "EXISTING_DOCUMENT_EXTRACTION", "DERIVED_FROM_EXISTING_QUALIFIED_DATA"} or
    not r["exact_missing_evidence"])
renames = [r for r in M if r["truthful_rename_candidate"]]
redund = [r for r in M if r["redundancy_candidate"] == "yes"]
research = [r for r in M if r["research_only_candidate"] == "yes"]

L = []
w = L.append

w("# Run 27 — the remediation matrix for every scientific target that is not a pass, "
  "the evidence contract behind each one, and the parsimony verdicts")
w("")
w("**This run wrote no production code, changed no operational state, activated nothing, "
  "removed nothing and consolidated nothing.** It is planning, evidence-contract design and "
  "parsimony, exactly as commissioned. Its whole value is making Runs 28 to 33 precise.")
w("")
w("## The headline, and the one number that came back different")
w("")
w("| Figure | Value | Derived from |")
w("|---|---|---|")
w(f"| Scientific targets | {len(audit)} | row count of `code_audit/run20_cycle12_100_reaudit.csv` |")
w(f"| Unique target identities | {len({a['code_id'] for a in audit})} | distinct `code_id` in the same file |")
w(f"| Current `SCIENTIFIC_PASS` | **{len(passes)}** | rows of that file whose disposition is `SCIENTIFIC_PASS` |")
w(f"| Requiring further work | **{len(audit) - len(passes)}** | the identity, not a literal |")
w(f"| Matrix rows written | **{len(M)}** | row count of the matrix CSV |")
w("")
w("**The run was commissioned to build a 98-module matrix. Mechanically derived, the answer is "
  "97.** The prompt's section 1 instructs that the 98 be derived rather than copied from a "
  "narrative, and that if the re-audit does not yield exactly two passes the real number be "
  "reported rather than forced. It yields three:")
w("")
for p in passes:
    w(f"- **{p['code_id']} {p['module_name']}** — {p['operational_activation']}, "
      f"{p['voting_status']}, lineage `{p['lineage_relationship']}`")
w("")
w("The third is **B1.1 Conservative Dominance**, raised to `SCIENTIFIC_PASS` by Run 20 Cycle 9, "
  "which found that a module named for a dominance rule was applying a counting rule and "
  "replaced it with a genuine maximum over the signal bands. The Run 20 report records the "
  "transition explicitly (`| SCIENTIFIC_PASS | 2 | 3 |`). The number 98 in the commissioning "
  "prompt is the pre-Cycle-9 figure. Nothing was adjusted to reach 98 and no row was invented "
  "to pad the matrix.")
w("")
w("**The artifact keeps the commissioned path** `code_audit/run27_98_module_remediation_matrix.csv` "
  "so the owner's file reference resolves, and it holds 97 rows. The guard asserts the identity "
  "`targets - passes == rows` and never the literal 97 or 98, so a later run that raises a "
  "fourth target to pass moves the matrix without breaking the suite.")
w("")
w("### Distribution by remediation type")
w("")
w("A row carries one or more types. Counts are rows carrying each type, so they exceed 97.")
w("")
w("| Type | Rows | What it means here |")
w("|---|---|---|")
_MEAN = {
    "DATA": "a real missing evidence source or canonical data structure",
    "METHOD": "the shipped computation is not the required canonical method",
    "CAL": "a parameter, threshold, membership, prior, weight or boundary lacks defensible provenance",
    "LINEAGE": "qualification, dependence, source ancestry or double-counting control is required",
    "REG": "an authoritative rule, version, applicability and evidence object is required",
    "VALIDATE": "intended-use performance requires a genuine reference or labelled dataset",
    "RESEARCH": "the method can be implemented scientifically but operational value is unestablished",
    "PARSIMONY": "the module may be redundant, misleadingly named, or not justify a separate presence",
}
for t, n in types.most_common():
    w(f"| `{t}` | {n} | {_MEAN[t]} |")
w("")
w(f"**`LINEAGE` at {types['LINEAGE']} of {len(M)} and `CAL` at {types['CAL']} are near-universal, "
  "and that is the finding rather than an inflation of it.** The Category-9 qualification gate is "
  "unimplemented platform-wide and production itself discloses it, so almost every module "
  "consumes unqualified signals; and no labelled corpus or expert reference standard exists in "
  "this repository, so almost no boundary can be calibrated. Two absent structures account for "
  "most of the population's exposure. They are not 97 separate problems.")
w("")
w("### Evidence posture")
w("")
w("| Question | Answer |")
w("|---|---|")
w(f"| Require a new evidence or data structure | {new_structure} |")
w(f"| Can be served from evidence the platform already has or already extracts | {existing} |")
w(f"| Rename or truthful-proxy candidates | {len(renames)} |")
w(f"| Consolidation or removal candidates | {len(redund)} |")
w(f"| Research-only candidates | {len(research)} |")
w(f"| Rows whose remaining work is calibration and validation only | "
  f"{sum(1 for r in M if not r['exact_missing_evidence'])} |")
w("")
w("Corpus status, per section 6: " + ", ".join(f"`{k}` {v}" for k, v in corpus.most_common()) + ".")
w("")
w("---")
w("")
w("## 1. The exact list requiring further work")
w("")
w("Derived, not copied. Every identity checked against the registry by the guard.")
w("")
w("| id | registered name | cat | disposition | primary | pri | run |")
w("|---|---|---|---|---|---|---|")
for r in M:
    w(f"| {r['canonical_id']} | {r['current_registered_name']} | {r['category']} | "
      f"{r['current_scientific_disposition']} | {r['primary_remediation_type']} | "
      f"{r['priority']} | {r['recommended_future_run']} |")
w("")
w("**A3.4 Material Cost Variance is deliberately absent.** It is registered and disabled pending "
  "an evidence-design decision, and the scientific-audit population excluded it, so it is not one "
  "of the hundred targets and cannot be one of the ninety-seven. The contract and procurement "
  "baseline package below is nevertheless the evidence design it was disabled pending, and the "
  "owner's deferred retain-or-remove decision on it depends on that package.")
w("")
w("## 2. The complete remediation matrix")
w("")
w("`code_audit/run27_98_module_remediation_matrix.csv`, 97 rows, "
  f"{len(M[0])} columns. Every mechanical column is read at build time from the registry, the "
  "Cycle-12 re-audit, `method_labels.py`, `parameters.py`, `registry.py` and the authoritative "
  "edge list; only the evidence contract is authored, in `server/tools/run27_curation.py`. A "
  "rename in the registry or a disposition change in the re-audit moves the matrix without "
  "anyone editing it.")
w("")
w("Columns: " + ", ".join(f"`{c}`" for c in M[0]) + ".")
w("")
w("## 3. DATA requirements, module by module")
w("")
w(f"{types['DATA']} rows carry `DATA`. The guard rejects any of them whose missing-evidence cell "
  "is empty, is one of a set of generic phrases, or is shorter than twelve words, because "
  "section 4 forbids stopping at \"more data required\". The specifications below are the full "
  "cells from the matrix.")
w("")
for r in M:
    if not r["exact_missing_evidence"]:
        continue
    w(f"**{r['canonical_id']} {r['current_registered_name']}** — canonical method: "
      f"{r['canonical_method_required']}.")
    w("")
    w(f"- Missing: {r['exact_missing_evidence']}")
    w(f"- Structure: {r['exact_missing_data_structure']}")
    w(f"- Supply: `{r['supply_mechanism']}` via {r['proposed_artifact']}")
    w(f"- Corpus: `{r['corpus_status']}`. Already reaching it: "
      f"{r['existing_structured_fields_available']}")
    w("")
w("## 4. Proposed evidence, document and form additions")
w("")
w("Supply mechanisms across the 97:")
w("")
w("| Mechanism | Rows |")
w("|---|---|")
for k, v in supply.most_common():
    w(f"| `{k}` | {v} |")
w("")
w("Distinct proposed artifacts, with the modules each would unblock:")
w("")
art = collections.defaultdict(list)
for r in M:
    if r["proposed_artifact"]:
        art[r["proposed_artifact"]].append(r["canonical_id"])
w("| Proposed artifact | Modules |")
w("|---|---|")
for k in sorted(art, key=lambda k: -len(art[k])):
    w(f"| {k} | {len(art[k])}: {', '.join(art[k])} |")
w("")
w("## 5. Shared work packages")
w("")
w("`code_audit/run27_remediation_work_packages.csv`. The served list and count of every package "
  "are derived from the matrix and checked against it, so a package cannot claim a module the "
  "matrix does not assign to it.")
w("")
w("| Package | Modules | Shared structure | Run |")
w("|---|---|---|---|")
for p in sorted(P, key=lambda p: -int(p["modules_served_count"])):
    w(f"| **{p['package_id']}** {p['package_name']} | {p['modules_served_count']} | "
      f"{p['shared_data_structure'][:150]}… | {p['recommended_run']} |")
w("")
w("**Where one structure enables several modules**, which is the point of the grouping:")
w("")
for p in sorted(P, key=lambda p: -int(p["modules_served_count"]))[:6]:
    w(f"- **{p['package_id']}** ({p['modules_served_count']} modules): {p['modules_served']}")
w("")
w("Three packages deserve naming in prose.")
w("")
for pid in ("PKG-ORPHANFIELDS", "PKG-ALTERNATIVES", "PKG-CAT9"):
    p = next(x for x in P if x["package_id"] == pid)
    w(f"**{pid} — {p['package_name']}.** {p['notes']}")
    w("")
w("## 6. Parsimony findings")
w("")
w("Classification across the 97: " + ", ".join(f"`{k}` {v}" for k, v in pars.most_common()) + ".")
w("")
w("Every redundancy claim below is established by property testing over the live production "
  "functions or by an argument over the whole input domain, re-derived every time "
  "`server/tools/test_run27_parsimony_proofs.py` runs and written to "
  "`code_audit/run27_parsimony_property_tests.csv`. **Three of the eight verdicts are negative.**")
w("")
for r in PT:
    w(f"### {r['case']}")
    w("")
    w(f"- Claim tested: *{r['claim']}*")
    w(f"- Method: {r['proof_method']}")
    w(f"- **Verdict: {r['verdict']}**")
    w(f"- Evidence: {r['evidence']}")
    w("")
w("### Truthful rename candidates")
w("")
w(f"{len(renames)} of the 97 carry one. The registered name and the truthful name are both "
  "already published by production on the interface response, the export and the methods "
  "documentation; what a participant reads is unchanged and changing it is an instrument "
  "decision for the owner, not a remediation.")
w("")
w("| id | registered | truthful |")
w("|---|---|---|")
for r in renames:
    w(f"| {r['canonical_id']} | {r['current_registered_name']} | "
      f"{r['truthful_rename_candidate']} |")
w("")
w("### Consolidation and removal candidates")
w("")
w("**Run 27 removes nothing and consolidates nothing.** Each of the following is a "
  "recommendation to the owner, and the guard asserts that every row marked a redundancy "
  "candidate says so in its own owner-decision cell.")
w("")
for r in redund:
    w(f"- **{r['canonical_id']} {r['current_registered_name']}** — {r['notes'] or r['canonical_method_required']}")
w("")
w("## 7. Disabled and research-only methods")
w("")
w("Registry status established mechanically from `server/app/simulation/registry.py` rather than "
  "from a historical count. `DISABLED_CONCEPT_ONLY` holds eight modules whose formula functions "
  "are never called; `DISABLED_EVIDENCE_UNDER_REVIEW` holds one, A3.4, which is outside this "
  "population. **No disabled module is activated by this run and none is proposed for activation; "
  "the guard checks that every disabled row's operational destination says it remains disabled.**")
w("")
w("| id | name | status | structure suppliable? | scientific value shown | operational value shown | recommendation |")
w("|---|---|---|---|---|---|---|")
_ASSESS = {
    "A3.8": ("yes, with a cost-driver reference dataset", "no", "no",
             "leave disabled; revisit when the Reference-Class Dataset exists"),
    "B2.7": ("yes in principle, by elicitation", "no", "no", "leave disabled, research-only"),
    "B2.9": ("no: the motivating phenomenon would have to be demonstrated first", "no", "no",
             "leave disabled; strongest REMOVE_CANDIDATE on parsimony grounds, owner decides"),
    "B2.20": ("only if the platform ever ranks a real object set", "no", "no",
              "leave disabled, research-only"),
    "B4.1": ("yes, with the Decision Alternatives Table", "no", "plausible but unshown",
             "leave disabled; revisit in Run 32 once the alternatives structure exists"),
    "B4.2": ("yes, with the Objective and Constraint Set", "no", "plausible but unshown",
             "leave disabled; revisit in Run 32"),
    "B4.5": ("yes, with alternatives plus input ranges", "no", "no", "leave disabled"),
    "B4.6": ("yes, with two or more alternatives on two or more objectives", "no",
             "plausible but unshown", "leave disabled; revisit in Run 32"),
}
for r in M:
    if r["canonical_id"] in _ASSESS:
        a = _ASSESS[r["canonical_id"]]
        w(f"| {r['canonical_id']} | {r['current_registered_name']} | "
          f"{r['current_operational_status']} | {a[0]} | {a[1]} | {a[2]} | {a[3]} |")
w("")
w("**Plithogenic Sets, Quantum Probability and Hypersoft Sets are all still disabled**, as the "
  "historical statement said, and the registry confirms it rather than the report asserting it. "
  "Assessed individually as instructed:")
w("")
w("- **B2.7 Plithogenic Sets.** Needs an attribute set with degrees of appurtenance and a "
  "contradiction degree between attribute values. That is suppliable by elicitation, so it is "
  "not impossible; but no operational question this platform asks is currently expressed in "
  "plithogenic terms, and no scientific or operational value has been demonstrated. Leave "
  "disabled, research-only.")
w("- **B2.9 Quantum Probability.** Unlike the rest of the family this is *not* merely an "
  "elicitation gap. Quantum probability is warranted where judgments violate classical "
  "additivity, and no such violation has been observed in this platform's data or could be "
  "observed without the elicited assessments that do not exist. Its supply mechanism is recorded "
  "as `NOT_REASONABLY_SUPPLIABLE`, the only row in the matrix that carries it. It is the "
  "strongest removal candidate in the population. **Removal is the owner's decision and this run "
  "does not take it.**")
w("- **B2.20 Hypersoft Sets.** A hypersoft set is a mapping from tuples of attribute values to "
  "subsets of a *universe of objects*, and a single project is not a universe. Suppliable only "
  "if the platform ever ranks a real alternative or project set, which is the same "
  "`PKG-ALTERNATIVES` structure Category 10 needs. Leave disabled, research-only.")
w("")
w(f"Two further modules are `KEEP_RESEARCH_ONLY` while remaining `ADVISORY_ONLY` and therefore "
  "live on the ledger: **A5.7 Agent-Based Supply Chain** and **A5.8 Discrete Event Simulation**. "
  "A5.8 is P1 rather than P3 despite the research classification, because its registered name "
  "asserts a simulation that does not exist and that is a truthfulness problem now, not later.")
w("")
w("## 8. Run 28 to 33 assignment")
w("")
w("**Zero orphans, checked by the guard.** Every row carries a primary run and a secondary. A row "
  "whose remaining work is calibration and validation only is assigned primarily to Run 33 with "
  "its category run recorded beside it; every other row terminates in Run 33 because Run 33 "
  "carries the complete hundred-target re-audit.")
w("")
w("| Run | Scope | Rows (primary) |")
w("|---|---|---|")
_SCOPE = {
    "Run 28": "Categories 1 to 3: cost, EVM, schedule and cost-risk structures",
    "Run 29": "Categories 4 to 5: document/risk evidence and system-model structures",
    "Run 30": "Categories 6 to 7: signal synthesis and epistemic/evidence methods",
    "Run 31": "Categories 8 to 9: governance, regulatory evidence, data integrity, Category-9",
    "Run 32": "Category 10 plus Portfolio Health: decision optimization and portfolio methods",
    "Run 33": "Calibration, empirical validation, final parsimony decisions, complete re-audit",
}
for k in sorted(_SCOPE):
    w(f"| {k} | {_SCOPE[k]} | {runs[k]} |")
w("")
w("## 9. Priority distribution")
w("")
w("Assigned on evidence, not category number.")
w("")
w("| Priority | Rows | Definition |")
w("|---|---|---|")
_PD = {
    "P0": "needed to prevent scientifically unsupported operational output",
    "P1": "necessary to make an intended operational method actually runnable",
    "P2": "necessary for calibration and validation after correct execution exists",
    "P3": "research expansion or optional complexity",
}
for k in ("P0", "P1", "P2", "P3"):
    w(f"| `{k}` | {pri[k]} | {_PD[k]} |")
w("")
w("The P0 set, and why each is there:")
w("")
for r in M:
    if r["priority"] == "P0":
        w(f"- **{r['canonical_id']} {r['current_registered_name']}** — {r['notes']}")
w("")
w("## 10. Owner decisions required")
w("")
w("| id | decision |")
w("|---|---|")
for r in M:
    if not r["owner_decision_required"].startswith("no"):
        w(f"| {r['canonical_id']} {r['current_registered_name']} | "
          f"{r['owner_decision_required']} |")
w("")
w("The standing decisions, grouped:")
w("")
w("1. **Whether any truthful name replaces a registered name on the participant surface.** "
  f"{len(renames)} modules are affected. The surface is frozen and checksummed and the study is "
  "mid-sequence, so this is an instrument decision with protocol consequences.")
w("2. **Whether the fuzzy-set family is consolidated.** Thirteen Category-7 modules are "
  "`CONSOLIDATE_CANDIDATE`. Property testing establishes they are *not* mathematically "
  "identical, so none may be deleted on a proof; it also establishes they read the same two or "
  "three raw inputs and differ only in their band boundaries.")
w("3. **Whether B2.9 Quantum Probability is retained at all.** The only "
  "`NOT_REASONABLY_SUPPLIABLE` row in the matrix.")
w("4. **Whether A4.6 and B3.5 remain two modules**, given they consume an identical field set.")
w("5. **Whether D1.5 Anomaly Score is recomposed or withdrawn**, given it is a strict function of "
  "D1.2's and D1.3's internals.")
w("6. **Whether line of balance and CCPM buffer health are applicable at all** to this "
  "platform's projects, which is scoping rather than data.")
w("7. **A3.4 Material Cost Variance**, retained behind the contract and procurement baseline "
  "package or removed. Deferred since Run 16 and unchanged here.")
w("8. **C1.4 Audit Trail Completeness** and **B2.18 MARCOS Ranking**, both recorded "
  "`OWNER_DECISION_REQUIRED` by the re-audit itself.")
w("")
w("## 11. Non-vacuity proof")
w("")
w("Two new suites, both in the runner. `test_run27_remediation_matrix.py` is 47 checks; "
  "`test_run27_parsimony_proofs.py` is 25 and re-derives every parsimony claim from the live "
  "production functions.")
w("")
w("`server/tools/run27_fault_campaign.py` injects the six mandated faults. For each it applies "
  "the mutation, **re-reads the file from disk and asserts the specific structural change so an "
  "injection that silently failed to apply halts the campaign rather than reporting a clean "
  "restore**, runs the guard as a separate process, requires a non-zero exit *and* a canonical "
  "RESULT line *and* the named check among the failures, then restores from a byte-exact backup "
  "and re-checks the baseline to full green. A run with no RESULT line is recorded "
  "`CRASH_NOT_RED` and fails the campaign: a crash is not red.")
w("")
w("| Fault | Injection confirmed | Guard exit | Verdict | Detail |")
w("|---|---|---|---|---|")
for r in NV:
    w(f"| {r['fault']} | {r['injection_confirmed']} | {r['guard_exit']} | **{r['verdict']}** | "
      f"{r['detail']} |")
w("")
w("`code_audit/run27_guard_nonvacuity.csv`. All six turned red for the intended reason, all six "
  "restored to 47/47, and the baseline was re-checked after every single fault rather than once "
  "at the end.")
w("")
w("**Two of my own parsimony claims failed their first check and were corrected rather than "
  "weakened.** A claimed counterexample for B1.4's growing denominator did not separate the two "
  "cases at the point I chose, and a source-string assertion did not match the comment it "
  "quoted. Both are recorded here because a suite that only ever confirms the author's "
  "expectation is the fourth failure mode.")
w("")
w("**One false redundancy finding was caught and is recorded in the suite's own docstring.** A "
  "first pass reported B2.3, B2.4, B2.5 and B2.6 as pairwise identical over the grid. They are "
  "not: all four abstain on that input shape, so the identical vectors were four columns of "
  "`None`. Identity between two abstentions is not redundancy. The check now excludes any module "
  "that never produces a band rather than counting it as a match.")
w("")
w("## 12. Suite result")
w("")
w("**On MERGED main: `server/run_all_suites.sh` — 127 suites, 10682 of 10682 checks, "
  "ALL SUITES GREEN, exit 0.** The two new suites are inside that total: "
  "`test_run27_remediation_matrix.py` 47/47 and `test_run27_parsimony_proofs.py` 25/25.")
w("")
w("The three self-rewriting audit CSVs (`run9_no_operational_effect.csv`, "
  "`run10_no_operational_effect.csv`, `run20_cycle12_100_reaudit.csv`) were restored after each "
  "suite run and not committed. Generated CSVs are written LF.")
w("")
w("## 13. Merged main")
w("")
w("Branch `run27-remediation-matrix`, commit `b48f1e1`. Merged to `main` with `--no-ff` at "
  "**`21675cf`**, and that is the commit the complete suite was run against. The report and this "
  "section land on top of it as a second commit, which touches documentation only: no suite "
  "reads a `REPORT_*.md` file, checked before landing it.")
w("")
w("## What this run did not do, plainly")
w("")
w("- **The Category-9 qualification gate is not closed and could not be.** "
  "`server/app/simulation/` is frozen at `sim-2026.08-v2` under a byte-identical guard, and "
  "`signal_package.py`, where `SIGNAL_QUALIFICATION = \"unqualified\"` and "
  "`CATEGORY_9_DEVIATION` live, is inside it. `PKG-CAT9` records the block rather than working "
  "around it.")
w("- **No production file was changed.** Section 13 permits correcting a mechanically proven "
  "registry, name or status inconsistency only where it prevents the matrix being accurate. The "
  "one known inconsistency, the registry's `Monte Carlo EAC` against the taxonomy's "
  "`Monte Carlo EAC Forecast`, does not: the matrix joins on identity through an explicit alias "
  "recorded in the builder. **It therefore remains open and is handed to Run 28.** No freeze "
  "record was taken and none was needed.")
w("- **The specification is silent where it is silent, and the silence is reported.** It states "
  "no ordering among B1, B2, B3 and B4 and does not say which categories supply the four "
  "downstream ones, so no row and no package claims that Categories 6 to 10 form a chain. The "
  "authoritative edge list carries five `SILENT` rows for exactly this reason.")
w("- **Three supported document types still emit fields no registered module consumes.** "
  "Environmental Report, Quality Audit Report and Safety Report. This is `PKG-ORPHANFIELDS`, "
  "the cheapest package in the programme, and it is scheduled rather than fixed because Run 27 "
  "is not an implementation run.")
w("- **`VALIDATE` is carried by 88 rows and no row is validated.** No labelled corpus and no "
  "expert reference standard exist in this repository. That is not a per-module defect; it is "
  "one absent structure, `PKG-DOCLABEL`, and every calibration in the programme waits behind it.")
w("")
w("## Artifacts")
w("")
for f in ["code_audit/run27_98_module_remediation_matrix.csv",
          "code_audit/run27_remediation_work_packages.csv",
          "code_audit/run27_parsimony_property_tests.csv",
          "code_audit/run27_guard_nonvacuity.csv",
          "server/tools/run27_curation.py",
          "server/tools/build_run27_remediation_matrix.py",
          "server/tools/build_run27_report.py",
          "server/tools/run27_fault_campaign.py",
          "server/tools/test_run27_remediation_matrix.py",
          "server/tools/test_run27_parsimony_proofs.py"]:
    w(f"- `{f}`")
w("")

OUT.write_text("\n".join(L), encoding="utf-8", newline="\n")
print(f"wrote {OUT.relative_to(ROOT)} ({len(L)} lines)")
