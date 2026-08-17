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
    CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY, DISABLED_EVIDENCE_UNDER_REVIEW, PROXY_QUALIFIERS,
    VALIDATED, load_registry,
)
from app.simulation.portfolio import PORTFOLIO_VALIDATED  # noqa: E402

NONE = "none in the repository"


def _archived() -> set[str]:
    """
    The identities whose operational runner refuses with disposition ARCHIVED.

    READ BY INTROSPECTION FROM THE ONE SOURCE, which is the `_refuse` call that built the runner.
    A second hand-kept list here would be a copy that can drift, and drift between a claim and
    its evidence is the whole defect this generator exists to prevent.
    """
    out = set()
    for mid, entry in VALIDATED.items():
        fn = entry[1] if isinstance(entry, tuple) else entry
        inner = getattr(fn, "__wrapped__", fn)
        if getattr(inner, "canonical_disposition", None) == "ARCHIVED":
            out.add(mid)
    return out


def _supplied_not_computed(registry: list[dict]) -> set[str]:
    """
    Registered identities the platform does NOT compute: no analytical runner and no portfolio
    runner implements them, so their value arrives supplied.

    Derived by set difference against the two dispatch tables rather than named, so a module that
    gains or loses an implementation cannot leave this statement stale.
    """
    return {m["new_id"] for m in registry
            if m["new_id"] not in VALIDATED and m["new_id"] not in PORTFOLIO_VALIDATED}


def runner_name(mid: str) -> str:
    """
    The runner a production dispatch actually reaches, resolved through `__wrapped__`.

    `functools.wraps` on the Category-9 qualification boundary copies the inner runner's
    __name__ and __module__ onto the wrapper, so naive introspection reports the wrapper as if it
    were the runner. `__wrapped__` is the honest answer to "which implementation executes".
    """
    entry = VALIDATED.get(mid)
    if entry is not None:
        fn = entry[1] if isinstance(entry, tuple) else entry
        inner = getattr(fn, "__wrapped__", fn)
        return f"{inner.__module__}.{inner.__name__}"
    if mid in PORTFOLIO_VALIDATED:
        return f"app.simulation.portfolio ({PORTFOLIO_VALIDATED[mid]})"
    return "none: declared in the registry and implemented by no runner"


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
    ARCHIVED = _archived()
    SUPPLIED_NOT_COMPUTED = _supplied_not_computed(registry)
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

    # RUN 30 CLOSURE. THE MAP IS READ FROM THE ANALYTICAL LAYER, NOT FROM ONE FILE OF IT. This
    # scanned canonical.py alone, so the eighteen Category-6 and -7 identities whose defining
    # structures live in canonical_v5.py were being described to a reader as "not required by
    # this module" on the very day their production routes started requiring one. The keys are
    # taken from the structure maps themselves rather than by pattern-matching a source file, so
    # a structure added to any layer cannot leave this statement stale.
    #
    # RUN 32 FINAL CLOSURE. THE RUN-30 LESSON WAS LEARNED AND THEN NOT APPLIED TWICE. Run 31 added
    # canonical_v6 (Categories 8 and 9) and Run 32 added canonical_v7 (Category 10), and NEITHER
    # was added to this list. The consequence is precisely the defect Run 30 wrote the comment
    # above about, at a larger scale: TWENTY-TWO identities -- A6.1, A6.2, A6.4, B3.1 to B3.5,
    # C1.1 to C1.7 and all seven of B4.1 to B4.7 -- were being told to a reader as "not required
    # by this module" while their production routes required a governed structure and abstained
    # without one.
    #
    # THE LAYER LIST IS NOW BUILT BY IMPORTING EVERY canonical_v* MODULE THAT EXISTS, rather than
    # by naming them. A future run that adds canonical_v8 cannot forget this file, because there
    # is no list here to forget to extend.
    import importlib                                                             # noqa: E402
    from app.simulation.canonical import CANONICAL_STRUCTURE_KEYS                # noqa: E402
    structure_maps: dict[str, dict[str, str]] = {"canonical": dict(CANONICAL_STRUCTURE_KEYS)}
    _sim_dir = ROOT / "server" / "app" / "simulation"
    _layer_files = sorted(_sim_dir.glob("canonical_v*.py"))
    for _p in _layer_files:
        _mod = importlib.import_module(f"app.simulation.{_p.stem}")
        for _attr in dir(_mod):
            if re.fullmatch(r"V\d+_STRUCTURE_KEYS", _attr):
                structure_maps[_p.stem] = dict(getattr(_mod, _attr))
    # EVERY canonical_v* FILE ON DISK MUST HAVE CONTRIBUTED ITS MAP. The count is derived from
    # the glob rather than written down, so this cannot be the stale list it is replacing: a
    # layer that exists but exports no structure map fails the build instead of being skipped
    # silently, which is exactly how v6 and v7 went missing for two runs.
    _missing = [p.stem for p in _layer_files if p.stem not in structure_maps]
    if _missing:
        raise SystemExit(
            f"these canonical layers exist but exported no V*_STRUCTURE_KEYS map: {_missing}; "
            f"refusing to generate a defensibility object from an incomplete layer list")
    canonical_ids: dict[str, str] = {}
    for _layer, _m in structure_maps.items():
        for _mid, _key in _m.items():
            canonical_ids.setdefault(_mid, _key)

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
        "",
        "   RUN 32 FINAL CLOSURE ADDED THE EXECUTION-STATE FIELDS, because one sentence was",
        "   being used for seven different situations and a reader could not tell them apart.",
        "     operationalState",
        "                  COMPUTES_FROM_AVAILABLE_EVIDENCE   computes now, from evidence held",
        "                  CONDITIONAL_ON_GOVERNED_STRUCTURE  canonical runner exists; needs a",
        "                                                     named structure; Not Estimable",
        "                                                     without it",
        "                  PORTFOLIO_COMPUTED                 computed across the portfolio",
        "                  DISABLED_CONCEPT_ONLY              engine exists, not operational",
        "                  DISABLED_EVIDENCE_UNDER_REVIEW     disabled pending an evidence",
        "                                                     -design decision",
        "                  ARCHIVED_FUTURE_RESEARCH           research record, not a runnable",
        "                                                     current capability",
        "                  SUPPLIED_VALUE                     consumed, not computed here",
        "     canonicalStructureRequired  whether the CURRENT production route requires a",
        "                  governed defining structure. Derived from every canonical layer's",
        "                  structure map, so a new layer cannot leave it stale.",
        "     definingStructure           the governed structure key itself, or null.",
        "     canonicalRunner             the implementation a production dispatch reaches,",
        "                  resolved through __wrapped__ past the Category-9 boundary.",
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
        # RUN 32 FINAL CLOSURE. THE EXECUTION STATEMENT WAS A BINARY AND THE INSTRUMENT IS NOT.
        # It said either "disabled: concept only" or "implemented and computed by the server",
        # and the second sentence was emitted for SEVENTY-SEVEN identities that do not currently
        # compute a project reading at all: they hold a canonical runner that requires a governed
        # defining structure, the controlled corpus does not carry it, and they return Not
        # Estimable. It was also emitted for the one value the platform is SUPPLIED rather than
        # computing (A4.1), for the module disabled pending an evidence-design decision (A3.4,
        # which is DISABLED_EVIDENCE_UNDER_REVIEW and not DISABLED_CONCEPT_ONLY, so the old test
        # missed it), and for the five portfolio-level readings.
        #
        # A READER CANNOT CHECK A CLAIM THAT CONFLATES THESE. The states are now distinguished,
        # and each sentence says only what the reader can verify against the running instrument.
        structure_key = canonical_ids.get(mid)
        if mid in ARCHIVED:
            state = "ARCHIVED_FUTURE_RESEARCH"
            implementation = ("historical implementation and scientific record are preserved, "
                              "but the method is not a runnable current capability")
        elif mid in DISABLED_EVIDENCE_UNDER_REVIEW:
            state = "DISABLED_EVIDENCE_UNDER_REVIEW"
            implementation = ("the module is disabled pending an evidence-design decision and "
                              "produces no live project reading")
        elif disabled:
            state = "DISABLED_CONCEPT_ONLY"
            implementation = ("the canonical laboratory engine exists, but the module is "
                              "operationally disabled and produces no live project reading")
        elif mid in SUPPLIED_NOT_COMPUTED:
            state = "SUPPLIED_VALUE"
            implementation = ("the platform consumes a governed supplied value rather than "
                              "computing the value as an analytical module")
        elif mid in PORTFOLIO_VALIDATED:
            state = "PORTFOLIO_COMPUTED"
            implementation = ("the current portfolio runner computes this reading across the "
                              "portfolio rather than from a single project's governed evidence")
        elif structure_key:
            state = "CONDITIONAL_ON_GOVERNED_STRUCTURE"
            implementation = ("the canonical production runner exists, but execution requires a "
                              "named defining structure; when that structure is absent the "
                              "module returns Not Estimable")
        else:
            state = "COMPUTES_FROM_AVAILABLE_EVIDENCE"
            implementation = ("the current production runner computes the canonical method from "
                              "the governed evidence the platform already holds")
        if mid in covered_run6:
            known = "known-answer case in the Run 6 suite"
        elif mid in covered_run4:
            known = "known-answer case in the Run 4 validate-the-seven suite"
        else:
            known = NONE
        boundary_status = ("domain and boundary enumeration recorded in a committed audit "
                           "artefact" if mid in boundary else NONE)
        # A DECLARED STRUCTURE IS NOT AN ENFORCED ONE WHEN NOTHING RUNS. A4.1 Document Risk
        # Score declares `documentRiskEvidence` in canonical_v4 and has NO runner at all: the
        # value is supplied to the platform. Saying the structure is "enforced by the
        # canonical-structure layer" would name an enforcement that no current route performs,
        # which is the same class of untrue statement this closure is removing everywhere else.
        if structure_key and state == "SUPPLIED_VALUE":
            canonical = ("declared in the canonical-structure layer but enforced by no current "
                         "route, because the platform does not compute this value")
            structure_required = False
        elif structure_key:
            canonical = "required and enforced by the canonical-structure layer"
            structure_required = True
        else:
            canonical = "not required by this module"
            structure_required = False
        voting = ("votes on the governed status" if mid in CORE_VOTING_MODULES
                  else "does not vote")
        if state in ("DISABLED_CONCEPT_ONLY", "DISABLED_EVIDENCE_UNDER_REVIEW",
                     "ARCHIVED_FUTURE_RESEARCH"):
            claim = "No claim. The module is disabled and does not compute."
        elif state == "SUPPLIED_VALUE":
            claim = ("No claim about server-side arithmetic. The platform does not compute this "
                     "value; it consumes a governed supplied value.")
        elif state == "CONDITIONAL_ON_GOVERNED_STRUCTURE":
            # THE ARITHMETIC CLAIM IS STILL TRUE AND IS STILL BOUNDED. A known-answer case proves
            # the method reproduces a hand-computed expected value; it says nothing about whether
            # the project currently supplies the structure the method needs.
            claim = (("Arithmetic independently verified for the stated formula, on a supplied "
                      "governed structure. No current project reading is produced without one.")
                     if known != NONE else
                     ("Implemented as stated. No independent verification of its arithmetic is "
                      "held in the repository, and no current project reading is produced "
                      "without its governed structure."))
        elif known != NONE:
            claim = "Arithmetic independently verified for the stated formula."
        else:
            claim = ("Implemented as stated. No independent verification of its arithmetic is "
                     "held in the repository.")
        qualification = ("Not validated and not calibrated. No empirical evidence of predictive "
                         "performance is held for this module.")
        if mid in PROXY_QUALIFIERS:
            qualification += " Stated proxy: " + PROXY_QUALIFIERS[mid] + "."
        # THE MACHINE-READABLE FIELDS EXIST SO A GUARD CAN CHECK THE OBJECT WITHOUT PARSING
        # PROSE. `operationalState` and `canonicalStructureRequired` are what the Run-32 closure
        # guard compares against the independently derived registry/runner/structure inventory.
        # `canonicalRunner` is here because the Run-30 finding was a correct library behind an
        # unchanged route: naming the runner makes a metadata swap to a historical proxy visible.
        lines.append(
            "    %s: { name: %s, implementation: %s, operationalState: %s, "
            "canonicalStructureRequired: %s, definingStructure: %s, canonicalRunner: %s, "
            "knownAnswer: %s, boundary: %s, "
            "calibration: %s, empirical: %s, canonicalStructure: %s, voting: %s, "
            "permittedClaim: %s, qualification: %s },"
            % (json.dumps(mid), json.dumps(name), json.dumps(implementation),
               json.dumps(state), "true" if structure_required else "false",
               json.dumps(structure_key) if structure_key else "null",
               json.dumps(runner_name(mid)),
               json.dumps(known), json.dumps(boundary_status),
               json.dumps("not calibrated; no calibration set exists in this repository"),
               json.dumps("not empirically validated; no comparison against real project "
                          "outcomes exists"),
               json.dumps(canonical), json.dumps(voting), json.dumps(claim),
               json.dumps(qualification)))
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
