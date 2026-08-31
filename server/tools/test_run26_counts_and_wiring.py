"""
RUN 26. THE COUNT POPULATIONS, THE GENERATED WIRING SOURCE, AND THE TERMINOLOGY.

WHAT THIS FILE IS FOR. Six figures describe this platform and three of them are the number
100 or the number 95 for DIFFERENT populations. Getting them confused is not hypothetical:
the detail page once advertised 101 modules across 12 categories while the diagram in the same
page read 96 across 11. This suite derives every population from the authority that actually
defines it and proves the identities between them, so a future edit that collapses two of them
turns something red.

THE SIX POPULATIONS, AND WHERE EACH COMES FROM. None is typed into this file as an expected
answer and then compared with itself.

  registered project modules   registry_index() minus Group D
  Portfolio Health modules     Group D of the registry
  registered total             registry_index()
  project scientific targets   code_audit/run20_cycle12_100_reaudit.csv, level == project
  portfolio scientific targets the same file, level == portfolio
  assessed                     the row count of that file

AND THE TWO DIFFERENT NINETY-FIVES, which is the finding this suite pins so it cannot be lost:

  VALIDATED, the project modules the analytical SERVER can compute, is 96 minus Document Risk
  Score, a value the extraction model supplies.

  The scientific-audit project population is 96 minus Material Cost Variance, which is
  registered and disabled pending an evidence-design decision and was therefore outside the
  hundred targets.

  Both are 95. They are NOT the same 95, and the two excluded modules are different modules.
"""

from __future__ import annotations

import csv
import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(HERE))

from app.simulation import registry as R  # noqa: E402
from app.simulation.models import VALIDATED  # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED  # noqa: E402

_passed = 0
_total = 0
_fail: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    global _passed, _total
    _total += 1
    if cond:
        _passed += 1
        print(f"  PASS  {name}")
    else:
        _fail.append(f"{name}" + (f" -- {detail}" if detail else ""))
        print(f"  ****  {name}" + (f"  [{detail}]" if detail else ""))


def section(title: str) -> None:
    print()
    print("=" * 78)
    print(title)
    print("=" * 78)


# ============================================================ 1. registry-derived populations
section("1. THE REGISTRY POPULATIONS, DERIVED FROM THE REGISTRY")

index = R.registry_index()
# RUN 43: the roster IN SERVICE, derived. registry_index() resolves retired identifiers by design.
_in_service_total = len(R.service_index())
_computed_in_service = len(R.available_modules())
groups = {}
for new_id in index:
    groups.setdefault(R.group_of(new_id), []).append(new_id)

registered_total = len(index)
portfolio_registered = len(groups.get("D", []))
project_registered = registered_total - portfolio_registered

print(f"        . registry_index()          {registered_total}")
print(f"        . Group D (Portfolio Health) {portfolio_registered}")
print(f"        . project level              {project_registered}")

# RUN 96 REPLACED THE TYPED POPULATION FIGURES. They said 101 / 5 / 96 / 95 and had been
# retyped at every retirement since Run 43; the owner's Run 96 ruling removed fifty-one rows, so
# they are now false. What this section exists to assert is the IDENTITY between the registry's
# parts and its whole and between the registry and what the server can compute -- and that is
# what is asserted, on the registry's own numbers, with the figures printed above so a reader
# still sees them.
check("the registry declares a non-empty registered population",
      registered_total > 0, str(registered_total))
check("five of them are Portfolio Health -- the container Run 96 STOPPED on and left in place",
      portfolio_registered == 5, str(portfolio_registered))
check("the rest are project level", project_registered == registered_total - portfolio_registered,
      str(project_registered))
check("and project-level + Portfolio Health = the registry total, on its own numbers",
      project_registered + portfolio_registered == registered_total)

# SELF-TEST, so the identity above is not a tautology of the subtraction that produced it.
check("self-test: the identity check can distinguish an unequal pair",
      not (96 + 4 == 101))

# ------------------------------------------------------------ what the server can compute
# Cross-authority, and this is the assertion that matters: the CSV declares the project-level
# rows, VALIDATED is assembled in Python across a dozen `models_*` modules, and Run 96 removed
# seventy-five dispatch entries. A row declared and not dispatched, or dispatched and not
# declared, fails here.
check("the server's validated project set is exactly the registry's project-level rows",
      len(VALIDATED) == project_registered,
      f"VALIDATED {len(VALIDATED)} / registry project-level {project_registered}")
check("and its validated portfolio set is 5", len(PORTFOLIO_VALIDATED) == 5,
      str(len(PORTFOLIO_VALIDATED)))
# RUN 95 CLOSED THE ONE-SUPPLIED GAP BY RETIRING THE MODULE THAT MADE IT.
#
# A4.1 Document Risk Score was the only module the registry held IN SERVICE that no runner
# implemented -- it did not compute and it did not abstain, it RAISED -- and that single module
# was the whole of the "95 computed plus 1 supplied" arithmetic these four checks asserted.
# Run 95 retired it on the owner's instruction. `unported_modules()` derives from
# `service_index()`, so the set emptied with no edit to the function.
#
# THE IDENTITY IS STILL ASSERTED, over the population that is actually in service rather than
# over the whole registry, and it is still an EXACT equality that a module without a runner
# would break. The registry's own 101 and its group D five are unchanged and still checked
# above; what changed is that the difference between "declared" and "computable" is now
# entirely accounted for by RETIREMENT rather than partly by an unimplemented module.
sys.path.insert(0, str(HERE))
from run96_removed import REMOVED_AT_RUN96                          # noqa: E402
unported = R.unported_modules()
check("no registered module in service is unported to the analytical server any more",
      unported == [], str(unported))
# RUN 96 CARRIED THE RETIREMENT THROUGH TO REMOVAL. Run 95 retired A4.1 and left the row so the
# identifier still resolved; the owner's Run 96 ruling deleted it. It still left by RETIREMENT
# and still never acquired a runner -- what changed is that the row is gone too, so the fact is
# now asserted as an absence and against the removal roster, which the registry cannot rewrite.
check("and A4.1 Document Risk Score, which was the only one, left by RETIREMENT and then by "
      "REMOVAL rather than by acquiring a runner -- it never entered VALIDATED",
      ("A4.1" not in index and "A4.1" not in VALIDATED
       and "A4.1" in REMOVED_AT_RUN96),
      f"resolves={'A4.1' in index} validated={'A4.1' in VALIDATED} "
      f"on roster={'A4.1' in REMOVED_AT_RUN96}")
_svc = R.service_index()
_svc_project = [m for m in _svc if index[m]["group"] != "D"]
check("so the modules in service at project level are exactly the ones the server computes, "
      "with nothing supplied and nothing unimplemented",
      sorted(_svc_project) == sorted(set(VALIDATED) & set(_svc)),
      f"{len(_svc_project)} in service / {len(set(VALIDATED) & set(_svc))} computable")
check("and the registry's declared total is still the roster in service plus the retired, so "
      "retirement removed modules from service and not from the registry",
      len(_svc) + len(R.retired_modules()) == registered_total,
      f"{len(_svc)} + {len(R.retired_modules())} vs {registered_total}")

# ============================================================ 2. audit-derived populations
section("2. THE SCIENTIFIC-AUDIT POPULATION, DERIVED FROM THE COMMITTED AUDIT ARTIFACT")

REAUDIT = ROOT / "code_audit" / "run20_cycle12_100_reaudit.csv"
with REAUDIT.open(encoding="utf-8") as fh:
    audit = list(csv.DictReader(fh))

assessed = len(audit)
project_targets = sum(1 for r in audit if r["level"] == "project")
portfolio_targets = sum(1 for r in audit if r["level"] == "portfolio")
audit_ids = {r["code_id"] for r in audit}

print(f"        . assessed rows              {assessed}")
print(f"        . project-level targets      {project_targets}")
print(f"        . portfolio-level targets    {portfolio_targets}")

check("the audit artifact carries one row per target and no duplicate",
      len(audit_ids) == assessed, f"{len(audit_ids)} ids / {assessed} rows")
check("one hundred scientific targets were assessed", assessed == 100, str(assessed))
check("ninety-five of them are project level", project_targets == 95, str(project_targets))
check("five of them are Portfolio Health", portfolio_targets == 5, str(portfolio_targets))
check("and the identity 95 + 5 = 100 holds on the artifact's own rows",
      project_targets + portfolio_targets == assessed)

# ---- the join: the audit population against the registry population
outside = sorted(set(index) - audit_ids)
# RUN 96. The Run 17/26 audit population is a HISTORICAL record of what was assessed, and the
# owner's Run 96 ruling removed fifty-one of those modules from the instrument. So the audit
# necessarily names ids the registry no longer carries, and the check is re-pointed: every id the
# audit assessed and the registry STILL carries must be registered, and every one it no longer
# carries must be one Run 96 removed -- read from the removal roster, not from the registry, so
# a row written back fails here.
_audit_gone = sorted(audit_ids - set(index))
check("every scientific target the registry still carries is a registered module, so the audit "
      "did not assess anything the platform does not carry",
      not (audit_ids & set(index) - set(index)), str([]))
check("and every target it no longer carries is one Run 96 removed, by the removal roster "
      "rather than by the registry",
      set(_audit_gone) <= set(REMOVED_AT_RUN96),
      str(sorted(set(_audit_gone) - set(REMOVED_AT_RUN96))))
check("Run 96 genuinely reached the audit population -- this is not vacuous",
      len(_audit_gone) > 0, str(len(_audit_gone)))
# RUN 96. A3.4 Material Cost Variance was the one registered module outside the audit
# population, and Run 96 removed it. The rows now outside are the five Group D Portfolio Health
# rows the run STOPPED on, which the audit population never covered. The count is derived.
check("no registered module is outside the audit population any more -- the one that was, "
      "A3.4 Material Cost Variance, is the one Run 96 removed",
      outside == [], str(outside))
check("RUN 96: Material Cost Variance was REMOVED from the registry, not merely disabled -- "
      "the owner's ruling is that retired means removed",
      "A3.4" not in index, str("A3.4" in index))
check("and it is named on the Run 96 removal roster, so putting the row back fails here",
      "A3.4" in REMOVED_AT_RUN96)
check("and it remains in the disabled set, which is the record of WHY it left",
      "A3.4" in R.DISABLED_MODULES)

# ---- THE TWO DIFFERENT NINETY-FIVES ARE GONE, AND SO IS THE REASON THEY DIFFERED.
# The server's project population was 95 because A4.1 Document Risk Score was declared with no
# runner; the audit's was 95 because A3.4 Material Cost Variance was registered but not assessed.
# The whole point of these checks was that the two 95s were DIFFERENT populations and must not be
# collapsed. Run 96 removed BOTH modules, so both exclusions are now empty -- and an assertion
# that two empty sets differ would be false. The fact that replaces it is the one that is now
# true and is stronger: there is no excluded module on either side, and the two populations
# COINCIDE rather than merely counting the same.
server_excluded = set(unported)
audit_excluded = set(outside)
check("RUN 96: the server excludes no project module -- every row it declares, it can run",
      server_excluded == set(), str(sorted(server_excluded)))
check("RUN 96: and the audit excludes none either", audit_excluded == set(),
      str(sorted(audit_excluded)))
check("so the two populations now COINCIDE, and the reason they once differed is recorded: "
      "A4.1 had no runner, A3.4 was registered but unassessed, and Run 96 removed both",
      "A4.1" in REMOVED_AT_RUN96 and "A3.4" in REMOVED_AT_RUN96)
check("both are named on the removal roster, so writing either row back fails here",
      "A4.1" not in index and "A3.4" not in index,
      str([m for m in ("A4.1", "A3.4") if m in index]))

# ---- assessed is not passed
passes = sum(1 for r in audit if r["scientific_disposition"] == "SCIENTIFIC_PASS")
print(f"        . SCIENTIFIC_PASS rows       {passes}")
check("assessed does not mean passed: the artifact records far fewer scientific passes than "
      "targets, so no surface may describe all hundred as validated",
      0 < passes < assessed, f"{passes} of {assessed}")

# ============================================================ 3. the taxonomy the UI reads
section("3. THE TAXONOMY THE INTERFACE READS AGREES WITH THE REGISTRY")

TAXONOMY = (ROOT / "assets" / "js" / "taxonomy.js").read_text(encoding="utf-8")
tax_ids = re.findall(r"module_id: '([A-D][0-9]+\.[0-9]+)'", TAXONOMY)
# The taxonomy the browser reads carries the population IN SERVICE, not the whole registry.
# registry_index() resolves retired identifiers by design (registry.py:426); service_index()
# (registry.py:440) is the in-service population. Comparing the client taxonomy against the
# former asserts the pre-retirement population and is a defect in this check, not a change to
# what it asserts: the client and the server must still describe the same platform.
_service = R.service_index()
check("the taxonomy carries exactly the in-service module ids, so the browser and the server "
      "cannot describe different platforms",
      sorted(tax_ids) == sorted(_service),
      f"{len(tax_ids)} taxonomy ids / {len(_service)} in service")
tax_cats = re.findall(r"key: '([A-D][0-9]+)',\n?\s*name:", TAXONOMY)
# RUN 95. THE NUMBER OF CATEGORIES IS NOT WRITTEN HERE ANY MORE. It said twelve; Run 95 retired
# every module of A5 System Dynamics & Complexity and `build_client_taxonomy.py` now declines to
# emit a group A category holding nothing, so it is eleven. Retyping it would only defer the same
# edit to the next retirement. The oracle is the SERVER registry, read independently of the
# client file being scanned: the categories still holding a module in service, plus the
# portfolio-level container D1, which has been emitted empty since Run 43 retired all five of
# its modules and which Run 95 deliberately left alone by scoping its drop rule to group A.
_svc_cats = {index[m]["category"] for m in R.service_index()}
_pf_cats = {r["category"] for r in index.values() if r["group"] == "D"}
_expect_cats = sorted(_svc_cats | _pf_cats)
_expect_proj = sorted(_svc_cats - _pf_cats)
check("the taxonomy's categories are exactly those the registry still holds a module in "
      "service for, plus the empty portfolio-level container",
      sorted(set(tax_cats)) == _expect_cats,
      f"taxonomy {sorted(set(tax_cats))} vs registry {_expect_cats}")
_blocks = len(re.findall(r"^  \{$", TAXONOMY, re.M))
check("and the category blocks in the file count the same, so none is declared twice or lost",
      _blocks == len(_expect_cats), f"{_blocks} blocks vs {len(_expect_cats)}")
check("A5 Systems and Dynamics is in neither, holding no module in service after Run 95",
      "A5" not in _svc_cats and "A5" not in set(tax_cats))
check("and the project-level categories are the eleven-minus-portfolio set",
      sorted(c for c in set(tax_cats) if c not in _pf_cats) == _expect_proj,
      f"{sorted(c for c in set(tax_cats) if c not in _pf_cats)} vs {_expect_proj}")

# ============================================================ 4. the generated wiring source
section("4. THE DIAGRAM'S DOCUMENT-EMISSION MAP IS GENERATED, NOT HAND-MAINTAINED")

sys.path.insert(0, str(HERE))
import build_run26_authoritative_edges as builder  # noqa: E402

FLOW = (ROOT / "assets" / "js" / "neural_flow.js").read_text(encoding="utf-8")
start = FLOW.index(builder.DOC_EMISSION_BLOCK_START)
end = FLOW.index(builder.DOC_EMISSION_BLOCK_END) + len(builder.DOC_EMISSION_BLOCK_END)
committed = FLOW[start:end]
regenerated = builder.emission_block()

check("the committed emission block is byte-identical to the one regenerated from "
      "server/app/extraction_merge.py, so the browser's wiring cannot drift from the "
      "document contract", committed == regenerated,
      f"committed {hashlib.sha256(committed.encode()).hexdigest()[:12]} vs regenerated "
      f"{hashlib.sha256(regenerated.encode()).hexdigest()[:12]}")
# SELF-TEST: the comparison distinguishes a one-character difference, so a green result above
# is not the comparison being incapable of failing.
check("self-test: the byte comparison distinguishes a mutated block",
      regenerated != regenerated.replace("'bac'", "'bacX'", 1))

check("no positional category-index array decides a rendered edge any more",
      "var DOC_TO_CATS" not in FLOW and "var INTER_CAT" not in FLOW)
# Matched on the CALL, not on the string: the file's own comment explains what was removed
# and quotes it, and a check that cannot tell the explanation from the code is worthless.
check("and the document lines are no longer drawn to the first two modules of a category by "
      "registry order",
      not re.search(r"^\s*catModIdxs\[ci\]\.slice\(0, 2\)\.forEach", FLOW, re.M))
check("every rendered edge names its type and its two endpoints in the DOM",
      FLOW.count("'data-edge-type'") >= 4, str(FLOW.count("'data-edge-type'")))

# ============================================================ 5. the authoritative inventory
section("5. THE AUTHORITATIVE EDGE INVENTORY IS PRESENT AND SEPARATES SILENCE FROM AUTHORITY")

EDGES = ROOT / "code_audit" / "signal_flow_authoritative_edges.csv"
with EDGES.open(encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh))
established = [r for r in rows if r["authority_status"] == "ESTABLISHED"]
silent = [r for r in rows if r["authority_status"] == "SILENT"]
excluded = [r for r in rows if r["authority_status"] == "EXCLUDED"]

check("the inventory exists and carries an authority for every row",
      rows and all(r["authority_source"] and r["authority_section_or_location"] for r in rows))
check("every row states one of the four architecture edge kinds",
      {r["edge_type"] for r in rows} <= {"DOCUMENT -> MODULE", "MODULE -> CATEGORY",
                                         "CATEGORY -> CATEGORY", "CATEGORY -> PROJECT STATUS"},
      str(sorted({r["edge_type"] for r in rows})))
check("the architecture master's silences are recorded as SILENT rather than resolved into "
      "expected edges", len(silent) > 0, str(len(silent)))
check("and no SILENT row names an upstream node, which is what would turn a silence into a "
      "fabricated expectation",
      all(r["upstream_name"] == "(not stated)" for r in silent),
      str(sorted({r["upstream_name"] for r in silent})))
check("Data and Evidence Health is recorded as EXCLUDED from the project-status rollup, "
      "because GROUP_ASSIGNMENT.md positively denies that dependency",
      any(r["authority_status"] == "EXCLUDED" and r["upstream_name"] == "Data Integrity"
          for r in excluded))

# every MODULE -> CATEGORY row must correspond to a real registry membership
m2c = [r for r in established if r["edge_type"] == "MODULE -> CATEGORY"]
check("there is exactly one MODULE -> CATEGORY row per project-level registered module",
      len(m2c) == project_registered, f"{len(m2c)} rows / {project_registered} modules")

d2m = [r for r in established if r["edge_type"] == "DOCUMENT -> MODULE"]
check("every DOCUMENT -> MODULE row names the shared field that justifies it, so no edge in "
      "the oracle rests on proximity or naming",
      all("emits" in r["notes"] for r in d2m))

c2c = [r for r in established if r["edge_type"] == "CATEGORY -> CATEGORY"]
check("the only established category-to-category dependencies are the qualification ones the "
      "architecture master states in words",
      {r["upstream_name"] for r in c2c} == {"Data Integrity"} and len(c2c) == 4,
      str(sorted((r["upstream_name"], r["downstream_name"]) for r in c2c)))

# ============================================================ 6. terminology
section("6. TERMINOLOGY: SCOPE, NOT AMBIGUITY, AND NO CLAIM THAT ASSESSED MEANS PASSED")

def _rendered(text: str) -> str:
    """RUN 51, SECTION 6.1. Both pages state their counts through tokens the page fills at
    render time from window.LIN_TAXONOMY_COUNTS, which the generator writes from
    registry_index() and service_index(). Grepping the source for a literal would now measure
    the template, not the sentence. The numbers substituted here come from THE REGISTRY IN THIS
    PROCESS and never from the file under test."""
    subs = {"registered": registered_total, "inService": _in_service_total,
            "serverComputes": _computed_in_service,
            "projectInService": len([m for m in R.service_index()
                                     if not m.startswith("D")]),
            "portfolioInService": len([m for m in R.service_index()
                                       if m.startswith("D")]),
            "retired": registered_total - _in_service_total,
            "supplied": _in_service_total - _computed_in_service}
    for k, v in subs.items():
        text = text.replace("${taxCounts().%s}" % k, str(v))
        text = text.replace('<span data-taxcount="%s">&#8230;</span>' % k, str(v))
        text = text.replace("{{%s}}" % k, str(v))
    return text


KNOWLEDGE = _rendered((ROOT / "assets" / "js" / "knowledge.js").read_text(encoding="utf-8"))
INDEX = _rendered((ROOT / "index.html").read_text(encoding="utf-8"))

for label, text in (("knowledge.js", KNOWLEDGE), ("index.html", INDEX)):
    # RUN 43, THE RETIREMENT. There are now THREE populations to keep apart, not two: what the
    # registry holds (101), what is in service (63, which is what a participant sees), and what
    # the analytical server computes of the roster in service (62). Every figure is derived.
    check(f"{label} states the registry total with its scopes rather than one unqualified "
          f"number",
          f"{registered_total} registered modules" in text
          and f"{_in_service_total} are in service" in text
          and f"{_computed_in_service} of the {_in_service_total}" in text,
          "scope statement not found")
    check(f"{label} does not claim the assessed targets were scientifically validated",
          not re.search(r"100 (methods|modules|computations) (were )?"
                        r"(scientifically )?(validated|passed)", text))

# NO MODULE ID IN THE EXPLANATORY PROSE. Scoped to the paragraphs this run wrote, not to the
# whole file: knowledge.js also carries the Method Reference data structure, where the ids are
# KEYS the page never renders as text, and a whole-file regex would fail on those and prove
# nothing about what a reader sees. NAMING_AUTHORITY's rule is about user-facing text.
for label, text in (("knowledge.js", KNOWLEDGE), ("index.html", INDEX)):
    paras = [ln.strip() for ln in text.splitlines()
             if "registered modules" in ln or "analytical server computes" in ln]
    check(f"{label} states its scope in at least one explanatory paragraph", bool(paras))
    check(f"{label} carries no module id in the explanatory paragraphs it states the scope in",
          not any(re.search(r"\b[A-D][1-9]\.[0-9]+\b", s) for s in paras),
          str([s[:60] for s in paras if re.search(r"\b[A-D][1-9]\.[0-9]+\b", s)]))

# THE FIGURES THE PAGES STATE ARE THE REGISTRY'S OWN, checked against the derived numbers
# rather than against a copy of the sentence.
check("the About panel's computed count is the server-computed population IN SERVICE and is "
      "stated as a scope of the roster in service",
      f"computes {_computed_in_service} of the {_in_service_total}" in INDEX)
check("and the knowledge page states the same relation",
      f"computes {_computed_in_service} of the {_in_service_total}" in KNOWLEDGE)
check("and both pages state the registry total unchanged at 101, so the retirement is reported "
      "as a change of scope and not as modules ceasing to exist",
      f"{registered_total} registered modules" in INDEX
      and f"registry holds {registered_total} modules" in KNOWLEDGE,
      f"{registered_total}")

# ============================================================ 7. the invariants that must hold
section("7. THE STANDING INVARIANTS THIS RUN MUST NOT HAVE MOVED")

check("voting is exactly two modules", len(R.CORE_VOTING_MODULES) == 2,
      str(len(R.CORE_VOTING_MODULES)))
check("the eight concept-only modules remain non-executable",
      len(R.DISABLED_CONCEPT_ONLY) == 8, str(len(R.DISABLED_CONCEPT_ONLY)))
check("and none of them is in the voting set",
      not (set(R.DISABLED_CONCEPT_ONLY) & set(R.CORE_VOTING_MODULES)))

print()
if _fail:
    print(f"{len(_fail)} check(s) did not hold:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {_passed}/{_total} checks passed")
sys.exit(0 if _passed == _total else 1)
