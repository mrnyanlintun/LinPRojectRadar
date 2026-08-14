#!/usr/bin/env python3
"""
RUN 26, STEP ONE. THE AUTHORITATIVE SIGNAL FLOW EDGE INVENTORY.

WRITTEN BEFORE ANY LINE OF THE SIGNAL FLOW RENDERER WAS READ FOR THE PURPOSE OF DERIVING AN
EXPECTED EDGE. The point of this file is that the oracle for Part 2 cannot come from
`assets/js/neural_flow.js`. This project has already produced two circular tests -- a chart
suite asserting against a hand-maintained copy of the server logic, and `test_period_series.py`
carrying a copy with the divisor defect it existed to catch -- and Addition A exists to stop a
third.

THE AUTHORITIES, IN ORDER, AND WHAT EACH ESTABLISHES

  1. `research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md`
     THE ARCHITECTURE MASTER. Its own metadata record declares it CONTROLLING for every audit
     or remediation run, and declares that repository source code is the object under test and
     never a source of theory. It establishes CATEGORY -> CATEGORY dependencies, and only
     those it states in words.

  2. `p0-baseline/module_renumbering_map.csv`, loaded through
     `server/app/simulation/registry.py`. THE MODULE REGISTRY. It establishes which category
     each registered module belongs to, and therefore every MODULE -> CATEGORY edge.

  3. `server/app/extraction_fields.py` and `server/app/extraction_merge.py`. THE DOCUMENT
     CONTRACT. Together they establish which signal keys a document type can emit. Crossed
     with the registry's per-module required inputs, they establish every DOCUMENT -> MODULE
     edge, by actual field consumption.

  4. `GROUP_ASSIGNMENT.md`. It establishes which groups reach project status: Group C does
     not contribute to project status, and Group D is portfolio level. That gives the
     CATEGORY -> PROJECT STATUS edges.

WHAT NO AUTHORITY ESTABLISHES is recorded with authority_status = SILENT and is deliberately
NOT part of the oracle. Every such row is a finding. Choosing an interpretation so that
implementation could proceed is exactly what Addition A forbids.
"""
from __future__ import annotations

import csv
import pathlib
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "code_audit" / "signal_flow_authoritative_edges.csv"

SPEC = "research/methodology/PCEIF_100_MODULE_SUPERVISORY_METHOD_SPECIFICATION_v1.md"
REGISTRY = "p0-baseline/module_renumbering_map.csv (via server/app/simulation/registry.py)"
DOCS = "server/app/extraction_fields.py + server/app/extraction_merge.py"
GROUPS = "GROUP_ASSIGNMENT.md"

# The user-facing category names, from the committed taxonomy. Keys are the registry's
# category codes; the names are the ones the taxonomy and the diagram both use.
CATEGORY_NAME = {
    "A1": "Cost and EVM Performance",
    "A2": "Schedule Performance",
    "A3": "Cost Risk",
    "A4": "Document-Derived Condition Signals",
    "A5": "System Dynamics and Complexity",
    "A6": "Delivery Quality Performance",
    "B1": "Signal Synthesis",
    "B2": "Evidence Combination",
    "B3": "Regulatory and Authority Thresholds",
    "B4": "Decision Optimization",
    "C1": "Data Integrity",
    "D1": "Portfolio Health",
}

# The project-level scope of the Signal Flow diagram: Portfolio Health is portfolio scale and
# is not on a single project's page (GROUP_ASSIGNMENT.md, "Group D is portfolio level").
PROJECT_CATEGORIES = [c for c in CATEGORY_NAME if c != "D1"]

# The four categories the architecture master names as consuming qualified governed objects
# rather than raw evidence. VERIFIED AGAINST THE MASTER, NOT TAKEN FROM THE BRIEF:
#   section 18, "Cats 6, 7, 8 and 10 must reject raw unqualified CPI/SPI/document-risk values
#   under the v0.5 target contract";
#   section 22 item 2, "downstream Cats 6/7/8/10 consume qualified governed objects";
#   section 15, "Category 6 creates NO new independent project evidence. It synthesizes
#   already qualified signal states."
# The master uses the pre-renumbering category scheme. Cats 6/7/8/10 map to B1/B2/B3/B4 by
# p0-baseline/module_renumbering_map.csv. Old Cat 8 split into A6 and B3; only the governance
# half, B3, carries the section-17 governance contract.
DERIVED = ["B1", "B2", "B3", "B4"]

# Section 18's target architecture: "Project Evidence -> Category 9 assessment -> Qualified
# Evidence -> analytical/governance use." Category 9 is C1 Data Integrity.
QUALIFIER = "C1"


def rows_category_to_category() -> list[dict]:
    out = []
    for dst in DERIVED:
        out.append(dict(
            upstream_type="CATEGORY", upstream_name=CATEGORY_NAME[QUALIFIER],
            downstream_type="CATEGORY", downstream_name=CATEGORY_NAME[dst],
            edge_type="CATEGORY -> CATEGORY",
            authority_source=SPEC,
            authority_section_or_location="section 18 (Category 9 target architecture) and "
                                          "section 22 item 2",
            authority_status="ESTABLISHED",
            notes="The master states raw evidence is qualified by Category 9 and that this "
                  "downstream category consumes qualified governed objects. The qualification "
                  "gate is the stated immediate dependency.",
        ))
    # Which analytical categories supply the signal states Signal Synthesis synthesizes is NOT
    # stated. Section 15 says "already qualified signal states" without enumerating a source.
    for dst in DERIVED:
        out.append(dict(
            upstream_type="CATEGORY", upstream_name="(not stated)",
            downstream_type="CATEGORY", downstream_name=CATEGORY_NAME[dst],
            edge_type="CATEGORY -> CATEGORY",
            authority_source=SPEC,
            authority_section_or_location="sections 15, 16, 17, 19",
            authority_status="SILENT",
            notes="The master states this category consumes qualified signal states or a "
                  "qualified project state, and never enumerates which categories supply "
                  "them. No edge is asserted. Reported as an unresolved architecture mapping.",
        ))
    # No ordering among the four downstream categories is stated anywhere in the master.
    out.append(dict(
        upstream_type="CATEGORY", upstream_name="(not stated)",
        downstream_type="CATEGORY", downstream_name="(ordering among B1, B2, B3, B4)",
        edge_type="CATEGORY -> CATEGORY",
        authority_source=SPEC,
        authority_section_or_location="sections 15, 16, 17, 19, 22",
        authority_status="SILENT",
        notes="The master never states that Signal Synthesis feeds Evidence Combination, nor "
              "any other ordering among the four downstream categories. The proposition in the "
              "brief that they form a chain is NOT established by the master and is not "
              "adopted.",
    ))
    return out


def rows_category_to_status() -> list[dict]:
    out = []
    for c in PROJECT_CATEGORIES:
        if c == QUALIFIER:
            out.append(dict(
                upstream_type="CATEGORY", upstream_name=CATEGORY_NAME[c],
                downstream_type="PROJECT STATUS", downstream_name="Project status",
                edge_type="CATEGORY -> PROJECT STATUS",
                authority_source=GROUPS,
                authority_section_or_location="'Group C does not contribute to project status'",
                authority_status="EXCLUDED",
                notes="Positively excluded by the authority. The edge must NOT be rendered.",
            ))
            continue
        out.append(dict(
            upstream_type="CATEGORY", upstream_name=CATEGORY_NAME[c],
            downstream_type="PROJECT STATUS", downstream_name="Project status",
            edge_type="CATEGORY -> PROJECT STATUS",
            authority_source=GROUPS,
            authority_section_or_location="'How to use this in user-facing text'; Group A and "
                                          "Group B contribute, Group C does not, Group D is "
                                          "portfolio level",
            authority_status="ESTABLISHED",
            notes="A project-level Group A or Group B category rolls up to project status.",
        ))
    return out


def module_rows() -> list[dict]:
    import csv as _csv
    with (ROOT / "p0-baseline" / "module_renumbering_map.csv").open(encoding="utf-8") as fh:
        return [r for r in _csv.DictReader(fh) if r["new_id"] not in ("-", "RETIRED")]


def rows_module_to_category(mods: list[dict]) -> list[dict]:
    display = module_display_names()
    out = []
    for m in mods:
        cat = m["category"]
        if cat == "D1":
            continue
        out.append(dict(
            upstream_type="MODULE",
            upstream_name=display.get(m["new_id"], m["module_name"]),
            downstream_type="CATEGORY", downstream_name=CATEGORY_NAME[cat],
            edge_type="MODULE -> CATEGORY",
            authority_source=REGISTRY,
            authority_section_or_location=f"row {m['new_id']}, category column",
            authority_status="ESTABLISHED",
            notes="Registry category membership: the module's output is one of the inputs the "
                  "category's state is formed from.",
        ))
    return out


def doc_emissions() -> dict[str, set[str]]:
    """doc_type -> the set of signal keys that document type can emit.

    Read from the document contract itself, not restated here.
    """
    # _EXTRA_NUMERIC_KEYS carries the emissions that do NOT flow through _NUMERIC_EMISSIONS:
    # the change-order branch and the two report types with derivation inputs. Reading only the
    # first table reported change_order, safety_report and subcontractor_report as emitting
    # nothing, which would have silently deleted their whole document column from the oracle.
    from app.extraction_merge import (
        _NUMERIC_EMISSIONS, _DATESTR_EMISSIONS, _EXTRA_NUMERIC_KEYS)
    from app.extraction_fields import DOC_TYPES
    out: dict[str, set[str]] = {t: set() for t in DOC_TYPES}
    for table in (_NUMERIC_EMISSIONS, _DATESTR_EMISSIONS, _EXTRA_NUMERIC_KEYS):
        for doc_type, pairs in table.items():
            out.setdefault(doc_type, set()).update(k for _, k in pairs if k)
    # `document_risk_score` is emitted for every document type whose extraction contract
    # requests it; extraction_merge pairs it explicitly rather than through the numeric table.
    from app.extraction_fields import extraction_fields_for
    for doc_type in list(out):
        if "document_risk_score" in extraction_fields_for(doc_type):
            out[doc_type].add("docRiskScore")
    return out


def module_display_names() -> dict[str, str]:
    """registry id -> the name the taxonomy renders, which is what a reader sees.

    A REAL NAMING DRIFT, RECORDED RATHER THAN PAPERED OVER: the registry calls A1.1 "Monte
    Carlo EAC" and the taxonomy renders "Monte Carlo EAC Forecast". The AUTHORITY for whether
    an edge exists is the registry and the document contract; the NAME on the rendered node is
    the taxonomy's. Joining the two on the id keeps the authority where it belongs and keeps
    the oracle comparable with what the browser actually draws.
    """
    import re
    text = (ROOT / "assets" / "js" / "taxonomy.js").read_text(encoding="utf-8")
    return {m.group(1): m.group(2) for m in
            re.finditer(r"num:\s*'([^']+)',\s*name:\s*'([^']+)'", text)}


def module_required() -> dict[str, list[str]]:
    """registry id -> its declared required signal keys, read from the committed taxonomy.

    KEYED ON THE REGISTRY ID, NOT THE DISPLAY NAME. The taxonomy calls A1.1 "Monte Carlo EAC
    Forecast" and the registry calls it "Monte Carlo EAC"; keying on the name silently dropped
    that module's whole document column. The id is the join both files agree on.
    """
    import re
    text = (ROOT / "assets" / "js" / "taxonomy.js").read_text(encoding="utf-8")
    out: dict[str, list[str]] = {}
    for m in re.finditer(r"\{\s*id:\s*'[^']+',\s*num:\s*'([^']+)',\s*name:\s*'[^']+'"
                         r".*?required:\s*\[([^\]]*)\]", text):
        keys = [k.strip().strip("'\"") for k in m.group(2).split(",") if k.strip()]
        out[m.group(1)] = keys
    return out


def rows_document_to_module(mods: list[dict]) -> tuple[list[dict], list[str]]:
    emissions = doc_emissions()
    required = module_required()
    display = module_display_names()
    by_id = {m["new_id"]: m for m in mods}
    unmatched = [i for i in required if i not in by_id]
    out = []
    for doc_type, keys in sorted(emissions.items()):
        for mod_id, req in sorted(required.items()):
            reg = by_id.get(mod_id)
            if reg is None or reg["category"] == "D1":
                continue
            mod_name = display.get(mod_id, reg["module_name"])
            shared = sorted(set(req) & keys)
            if not shared:
                continue
            out.append(dict(
                upstream_type="DOCUMENT", upstream_name=doc_type,
                downstream_type="MODULE", downstream_name=mod_name,
                edge_type="DOCUMENT -> MODULE",
                authority_source=DOCS + "; " + REGISTRY,
                authority_section_or_location="_NUMERIC_EMISSIONS/_DATESTR_EMISSIONS for "
                                              f"{doc_type}; required inputs for "
                                              f"{reg['new_id']}",
                authority_status="ESTABLISHED",
                notes="The document type emits " + ", ".join(shared)
                      + ", which this module declares as a required input.",
            ))
    return out, unmatched


DOC_EMISSION_BLOCK_START = "  // ---BEGIN GENERATED DOCUMENT EMISSIONS---"
DOC_EMISSION_BLOCK_END = "  // ---END GENERATED DOCUMENT EMISSIONS---"


def emission_block() -> str:
    """The doc_type -> emitted signal keys map, as the exact JS block neural_flow.js carries.

    THE BROWSER MUST NOT CARRY ITS OWN OPINION OF WHICH DOCUMENT FEEDS WHICH MODULE. The old
    diagram wired each document to the FIRST TWO modules of a category by registry order, which
    Addition A forbids by name. The wiring is now derived in the browser from this map crossed
    with each module's declared required inputs -- the same two authorities this file uses --
    and the map is GENERATED here rather than hand-maintained, so it cannot drift from the
    document contract. `server/tools/test_run26_counts_and_wiring.py` regenerates it and fails
    if the committed bytes differ.
    """
    em = doc_emissions()
    lines = [DOC_EMISSION_BLOCK_START,
             "  // GENERATED by server/tools/build_run26_authoritative_edges.py from",
             "  // server/app/extraction_merge.py. Do not edit by hand: the suite regenerates",
             "  // this block and fails if the bytes differ.",
             "  var DOC_EMISSIONS = {"]
    for doc_type in sorted(em):
        keys = sorted(em[doc_type])
        lines.append(f"    '{doc_type}': [" + ",".join(f"'{k}'" for k in keys) + "],")
    lines.append("  };")
    lines.append(DOC_EMISSION_BLOCK_END)
    return "\n".join(lines)


def sync_emission_block() -> bool:
    """Rewrite the generated block inside neural_flow.js. Returns True if the bytes changed."""
    target = ROOT / "assets" / "js" / "neural_flow.js"
    text = target.read_text(encoding="utf-8")
    if DOC_EMISSION_BLOCK_START not in text:
        raise SystemExit("neural_flow.js carries no generated-emissions block to sync")
    head, _, rest = text.partition(DOC_EMISSION_BLOCK_START)
    _, _, tail = rest.partition(DOC_EMISSION_BLOCK_END)
    new = head + emission_block() + tail
    if new == text:
        return False
    target.write_text(new, encoding="utf-8", newline="")
    return True


def main() -> None:
    if "--sync-emissions" in sys.argv:
        print("emissions block changed" if sync_emission_block() else "emissions block current")
    mods = module_rows()
    rows = []
    d2m, unmatched = rows_document_to_module(mods)
    rows += d2m
    rows += rows_module_to_category(mods)
    rows += rows_category_to_category()
    rows += rows_category_to_status()
    cols = ["upstream_type", "upstream_name", "downstream_type", "downstream_name",
            "edge_type", "authority_source", "authority_section_or_location",
            "authority_status", "notes"]
    with OUT.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    est = sum(1 for r in rows if r["authority_status"] == "ESTABLISHED")
    print(f"wrote {OUT}")
    print(f"  rows            {len(rows)}")
    print(f"  ESTABLISHED     {est}")
    print(f"  SILENT          {sum(1 for r in rows if r['authority_status'] == 'SILENT')}")
    print(f"  EXCLUDED        {sum(1 for r in rows if r['authority_status'] == 'EXCLUDED')}")
    for t in ("DOCUMENT -> MODULE", "MODULE -> CATEGORY", "CATEGORY -> CATEGORY",
              "CATEGORY -> PROJECT STATUS"):
        n = sum(1 for r in rows if r["edge_type"] == t and r["authority_status"] == "ESTABLISHED")
        print(f"  {t:32s} {n}")
    if unmatched:
        print(f"  taxonomy names not found in the registry: {unmatched}")


if __name__ == "__main__":
    main()
