#!/usr/bin/env python3
"""
RUN 11, GATE 4. Generates assets/js/ds_defensibility_evidence.js from the controlling registry
and the committed audit artefacts.

WHY A GENERATOR AND NOT AN EDIT. The handbook carried a hand-authored defensibility claim per
module. A hand-authored claim drifts: the module gains a domain guard, loses a band source, stops
computing entirely, and the sentence beside it says what it said before. Sixty-nine of them said
"Validated by ..." about a platform that holds no validation evidence for any module. Deriving
the evidence statuses from the registry means the claim cannot outlive the evidence.

    python tools/build_run11_defensibility_evidence.py            # writes the file
    python tools/build_run11_defensibility_evidence.py --stdout   # prints it, for the suite
"""
from __future__ import annotations

import csv
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "server"))

from app.simulation.registry import (  # noqa: E402
    CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY, PROXY_QUALIFIERS, load_registry,
)

NONE = "none in the repository"


def _set_literal(text: str, name: str) -> set[str]:
    i = text.index(name + " = {")
    j = text.index("}", i)
    return set(re.findall(r'"([A-D]\d+\.\d+)"', text[i:j]))


def _csv_ids(path: pathlib.Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(encoding="utf-8-sig") as f:
        return {r["module_id"].strip() for r in csv.DictReader(f) if r.get("module_id")}


def build() -> str:
    registry = load_registry()
    run6 = (ROOT / "server" / "tools" / "test_run6_known_answer.py").read_text(encoding="utf-8")
    covered_run6 = _set_literal(run6, "COVERED_HERE")
    covered_run4 = _set_literal(run6, "COVERED_BY_RUN_4")

    audit = ROOT / "code_audit"
    boundary = set()
    for name in ("run8_module_test_results.csv", "run10_bucket2_scope.csv",
                 "run10_neighbour_sweep.csv", "run10b_bucket3_integration.csv",
                 "run10b_bucket4_integration.csv", "run10b_neighbour_findings.csv",
                 "run11_neighbour_defects_fixed.csv"):
        boundary |= _csv_ids(audit / name)

    canonical_src = (ROOT / "server" / "app" / "simulation" / "canonical.py").read_text(
        encoding="utf-8")
    canonical_ids = set(re.findall(r'"([A-D]\d+\.\d+)"', canonical_src))

    lines = [
        "/* GENERATED FILE. Do not edit by hand.",
        "",
        "   RUN 11, GATE 4. THE DEFENSIBILITY EVIDENCE STATUS OF EVERY REGISTERED COMPUTATION,",
        "   DERIVED FROM THE CONTROLLING REGISTRY AND THE COMMITTED AUDIT ARTEFACTS.",
        "",
        "   Written by tools/build_run11_defensibility_evidence.py. Nothing here is hand-authored,",
        "   which is the point: the handbook carried a separate hand-maintained claim per module,",
        "   and a hand-maintained claim is one that can drift away from its evidence without",
        "   anything noticing. Sixty-nine of them said a module was validated.",
        "",
        "   WHAT THE FIELDS MEAN, AND WHAT THEY DELIBERATELY DO NOT SAY.",
        "     knownAnswer  the repository holds a case with a hand-computed expected value for",
        "                  this module's stated formula, and the module reproduces it. That",
        "                  supports the sentence 'Arithmetic independently verified for the",
        "                  stated formula.' It is not validation and it is not calibration.",
        "     boundary     the repository holds a domain and boundary enumeration for it.",
        "     calibration  none is held for any module here. No parameter was fitted to observed",
        "                  outcomes and no calibration set exists.",
        "     empirical    none is held for any module here. No module has been compared against",
        "                  real project outcomes.",
        "*/",
        "const DS_DEFENSIBILITY_EVIDENCE = {",
        '  generatedFrom: "server/app/simulation/registry.py and the committed code_audit '
        'artefacts",',
        '  permittedClaimForKnownAnswer: "Arithmetic independently verified for the stated '
        'formula.",',
        '  calibrationStatusPlatformWide: "Not calibrated. No calibration set or fitted '
        'parameter exists in this repository.",',
        '  empiricalValidationStatusPlatformWide: "Not empirically validated. No comparison '
        'against real project outcomes exists in this repository.",',
        "  modules: {",
    ]

    for m in registry:
        mid, name = m["new_id"], m["module_name"]
        disabled = mid in DISABLED_CONCEPT_ONLY
        implementation = ("disabled: concept only, refused before its formula is reached"
                          if disabled else "implemented and computed by the server")
        if mid in covered_run6:
            known = "known-answer case in the Run 6 suite"
        elif mid in covered_run4:
            known = "known-answer case in the Run 4 validate-the-seven suite"
        else:
            known = NONE
        boundary_status = ("domain and boundary enumeration recorded in a committed audit "
                           "artefact" if mid in boundary else NONE)
        canonical = ("required and enforced by the canonical-structure layer"
                     if mid in canonical_ids else "not required by this module")
        voting = ("votes on the governed status" if mid in CORE_VOTING_MODULES
                  else "does not vote")
        if disabled:
            claim = "No claim. The module is disabled and does not compute."
        elif known != NONE:
            claim = "Arithmetic independently verified for the stated formula."
        else:
            claim = ("Implemented as stated. No independent verification of its arithmetic is "
                     "held in the repository.")
        qualification = ("Not validated and not calibrated. No empirical evidence of predictive "
                         "performance is held for this module.")
        if mid in PROXY_QUALIFIERS:
            qualification += " Stated proxy: " + PROXY_QUALIFIERS[mid] + "."
        lines.append(
            "    %s: { name: %s, implementation: %s, knownAnswer: %s, boundary: %s, "
            "calibration: %s, empirical: %s, canonicalStructure: %s, voting: %s, "
            "permittedClaim: %s, qualification: %s },"
            % tuple(json.dumps(x) for x in (
                mid, name, implementation, known, boundary_status,
                "not calibrated; no calibration set exists in this repository",
                "not empirically validated; no comparison against real project outcomes exists",
                canonical, voting, claim, qualification)))
    lines += ["  }", "};",
              "if (typeof window !== 'undefined') "
              "window.DS_DEFENSIBILITY_EVIDENCE = DS_DEFENSIBILITY_EVIDENCE;"]
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    out = build()
    if "--stdout" in sys.argv:
        sys.stdout.write(out)
    else:
        target = ROOT / "assets" / "js" / "ds_defensibility_evidence.js"
        target.write_text(out, encoding="utf-8")
        print(f"wrote {target}")
