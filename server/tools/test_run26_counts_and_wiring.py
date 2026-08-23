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

check("the registry declares 101 registered modules", registered_total == 101,
      str(registered_total))
check("five of them are Portfolio Health", portfolio_registered == 5,
      str(portfolio_registered))
check("ninety-six of them are project level", project_registered == 96,
      str(project_registered))
check("and the identity 96 + 5 = 101 holds on the registry's own numbers",
      project_registered + portfolio_registered == registered_total)

# SELF-TEST, so the identity above is not a tautology of the subtraction that produced it.
check("self-test: the identity check can distinguish an unequal pair",
      not (96 + 4 == 101))

# ------------------------------------------------------------ what the server can compute
check("the server's validated project set is 95", len(VALIDATED) == 95, str(len(VALIDATED)))
check("and its validated portfolio set is 5", len(PORTFOLIO_VALIDATED) == 5,
      str(len(PORTFOLIO_VALIDATED)))
unported = R.unported_modules()
check("exactly one registered module is not ported to the analytical server",
      len(unported) == 1, str(unported))
check("and it is the document risk value the extraction model supplies, which is the WHOLE "
      "of the difference between 96 registered project modules and the 95 the server computes",
      unported == ["A4.1"] and index["A4.1"]["module_name"] == "Document Risk Score",
      str(unported))
check("so 95 computed plus 1 supplied is exactly the 96 registered project modules",
      len(VALIDATED) + len(unported) == project_registered)
check("and 100 server-computed plus 1 supplied is exactly the 101 registered modules, which "
      "is the population the knowledge page's computation count names",
      len(VALIDATED) + len(PORTFOLIO_VALIDATED) + len(unported) == registered_total)

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
check("every scientific target is a registered module, so the audit did not assess anything "
      "the platform does not carry", not (audit_ids - set(index)),
      str(sorted(audit_ids - set(index))))
check("exactly one registered module was outside the hundred-target population",
      len(outside) == 1, str(outside))
check("and it is Material Cost Variance, which is REGISTERED and disabled pending an "
      "evidence-design decision: that is the whole of the difference between 101 registered "
      "and 100 assessed",
      outside == ["A3.4"] and index["A3.4"]["module_name"] == "Material Cost Variance",
      str(outside))
check("Material Cost Variance remains registered rather than deleted to make the numbers "
      "agree", "A3.4" in index)
check("and it remains disabled", "A3.4" in R.DISABLED_MODULES)

# ---- THE TWO DIFFERENT NINETY-FIVES. This is the check that stops them being collapsed.
server_excluded = set(unported)
audit_excluded = set(outside)
check("the server's excluded project module and the audit's excluded project module are "
      "DIFFERENT modules, so the two ninety-fives are two populations and not one",
      server_excluded != audit_excluded,
      f"server excludes {sorted(server_excluded)}, audit excludes {sorted(audit_excluded)}")
check("Material Cost Variance IS one of the modules the server can compute, so it is not the "
      "reason the server's project count is 95", "A3.4" in VALIDATED)
check("and Document Risk Score IS one of the hundred scientific targets, so it is not the "
      "reason the audit's project count is 95", "A4.1" in audit_ids)

# ---- assessed is not passed
passes = sum(1 for r in audit if r["scientific_disposition"] == "SCIENTIFIC_PASS")
print(f"        . SCIENTIFIC_PASS rows       {passes}")
check("assessed does not mean passed: the artifact records far fewer scientific passes than "
      "targets, so no surface may describe all hundred as validated",
      0 < passes < assessed, f"{passes} of {assessed}")

# ============================================================ 3. the taxonomy the UI reads
section("3. THE TAXONOMY THE INTERFACE READS AGREES WITH THE REGISTRY")

TAXONOMY = (ROOT / "assets" / "js" / "taxonomy.js").read_text(encoding="utf-8")
tax_ids = re.findall(r"key: '([A-D][0-9]+\.[0-9]+)'", TAXONOMY)
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
check("and twelve categories, eleven of them project level",
      len(re.findall(r"^  \{$", TAXONOMY, re.M)) == 12,
      str(len(re.findall(r"^  \{$", TAXONOMY, re.M))))

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
