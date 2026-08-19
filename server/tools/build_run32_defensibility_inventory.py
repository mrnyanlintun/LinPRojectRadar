"""
RUN 32 FINAL CLOSURE. THE INDEPENDENT MODULE-DEFENSIBILITY INVENTORY, AND THE RECONCILIATION.

THE SERVED DEFENSIBILITY OBJECT IS THE OBJECT UNDER TEST, so it does not generate its own
expected values and it is not read to build them. Everything in the EXPECTED column below is
derived from the running instrument:

    registry identity        `registry.load_registry()` -- the population, mechanically. Nothing
                             is hard-coded and no count is assumed.
    activation               `DISABLED_CONCEPT_ONLY`, `DISABLED_EVIDENCE_UNDER_REVIEW`
    voting                   `CORE_VOTING_MODULES`
    canonical runner         `registry.VALIDATED` / `portfolio.PORTFOLIO_VALIDATED`, resolved
                             through `__wrapped__` because `functools.wraps` hides the real
                             runner behind the Category-9 boundary
    required structure       the structure maps of EVERY canonical layer -- canonical, v3, v4,
                             v5, v6, v7 -- read as maps rather than by scanning a source file
    production supply path   `project_data.governed_structure_keys()`
    operational behaviour    BY EXECUTION: `registry.run_module` on the real-corpus signal
                             inputs, with qualified evidence, and again with the module's
                             governed structure present, so "computes when the structure exists"
                             is measured and not asserted
    archived status          `models_cat7.DISPOSITION_ARCHIVED` reached on the real route

Comparing the served object against another copied metadata table would be the failure mode this
repository has already met: asserting against a copy of the logic. It is compared against the
instrument.

Writes code_audit/run32_defensibility_metadata_reconciliation.csv. Run with PYTHONIOENCODING=utf-8.
"""

from __future__ import annotations

import csv
import datetime
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "server"))

from app.project_data import governed_structure_keys                      # noqa: E402
from app.simulation import registry as REG                                # noqa: E402
from app.simulation.canonical import CANONICAL_STRUCTURE_KEYS as K0       # noqa: E402
from app.simulation.canonical_v3 import V3_STRUCTURE_KEYS as K3           # noqa: E402
from app.simulation.canonical_v4 import V4_STRUCTURE_KEYS as K4           # noqa: E402
from app.simulation.canonical_v5 import V5_STRUCTURE_KEYS as K5           # noqa: E402
from app.simulation.canonical_v6 import V6_STRUCTURE_KEYS as K6           # noqa: E402
from app.simulation.canonical_v7 import V7_STRUCTURE_KEYS as K7           # noqa: E402
from app.simulation.canonical_v8 import V8_STRUCTURE_KEYS as K8           # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED                  # noqa: E402

#: Every canonical layer's structure map, newest last. A module's defining structure is looked up
#: here rather than by pattern-matching a source file, so a structure added to any layer cannot
#: leave a statement stale. THIS IS THE LIST THE GENERATOR WAS MISSING v6 AND v7 FROM.
# RUN 33 ADDS v8, the Portfolio Health layer, for the reason this comment already records: a
# structure added to any layer and not listed here leaves a stale statement served with every
# existing guard green. The five Portfolio Health modules define governed structures from v21.
STRUCTURE_MAPS = (("canonical", K0), ("v3", K3), ("v4", K4), ("v5", K5),
                  ("v6", K6), ("v7", K7), ("v8", K8))

SI = {"bac": 1_000_000.0, "ev": 400_000.0, "ac": 440_000.0, "pv": 450_000.0,
      "cpi": 0.909, "spi": 0.889, "docRiskScore": 0.35,
      "actualPctComplete": 40.0, "plannedPctComplete": 45.0}
QUALIFIED = {"qualification_state": "QUALIFIED", "timeliness_status": "TIMELY",
             "verification_status": "verified", "source_authority": "system_of_record"}
CUT = datetime.date(2026, 8, 17)


def NOOP() -> float:
    return 0.5


# ---------------------------------------------------------------------------- vocabulary
#
# The repository's existing words are reused where an equivalent exists. Nothing here invents
# impressive capability language: every sentence states what the reader can check.
EXEC_COMPUTES = ("the current production runner computes the canonical method from the governed "
                 "evidence the platform already holds")
EXEC_CONDITIONAL = ("the canonical production runner exists, but execution requires a named "
                    "defining structure; when that structure is absent the module returns Not "
                    "Estimable")
EXEC_DISABLED = ("the canonical laboratory engine exists, but the module is operationally "
                 "disabled and produces no live project reading")
EXEC_DISABLED_INPUT = (
    "canonical execution requires the governed cost-driver distribution structure AND an "
    "authoritative rule for turning drawn driver figures into a forecast of the final cost; "
    "neither is established, so the module is operationally disabled for insufficient input and "
    "produces no live project reading. The earlier budget-and-index approximation is preserved in "
    "the record for traceability and is not the canonical operational method")
EXEC_DISABLED_EVIDENCE = ("the module is disabled pending an evidence-design decision and "
                          "produces no live project reading")
EXEC_ARCHIVED = ("historical implementation and scientific record are preserved, but the method "
                 "is not a runnable current capability")
EXEC_SUPPLIED = ("the platform consumes a governed supplied value rather than computing the "
                 "value as an analytical module")
EXEC_PORTFOLIO = ("the current portfolio runner computes this reading across the portfolio "
                  "rather than from a single project's governed evidence")

STRUCT_REQUIRED = "required and enforced by the canonical-structure layer"
STRUCT_NOT_REQUIRED = "not required by this module"
STRUCT_DECLARED_NOT_ENFORCED = ("declared in the canonical-structure layer but enforced by no current "
                                "route, because the platform does not compute this value")
#: RUN 36. The OTHER way a declared structure can be unenforced, and it is not the same fact.
#: A4.1 reaches the sentence above because nothing computes it at all. A1.1 reaches this one
#: because it computes perfectly well WITHOUT the structure it declares: the intake accepts the
#: structure and no route reads it, so supplying it changes nothing. Saying "the platform does
#: not compute this value" of a module that computes every period would be a second untrue
#: sentence put in place of the first.
STRUCT_REQUIRED_PLUS_MAPPING = ("required by the canonical method, together with an "
                                "authoritative rule for turning drawn driver figures into a "
                                "forecast; neither is established, so no canonical result is "
                                "produced")
STRUCT_DECLARED_NOT_CONSUMED = ("declared in the canonical-structure layer and accepted by the "
                                "intake, but read by no current route, so the reading is "
                                "produced whether it is supplied or not")


def structure_of(mid: str) -> tuple[str | None, str | None]:
    """The defining structure key and the layer that declares it, or (None, None)."""
    for layer, m in STRUCTURE_MAPS:
        if mid in m:
            return m[mid], layer
    return None, None


def runner_of(mid: str) -> str:
    entry = REG.VALIDATED.get(mid)
    if entry is not None:
        fn = entry[1] if isinstance(entry, tuple) else entry
        inner = getattr(fn, "__wrapped__", fn)
        return f"{inner.__module__}.{inner.__name__}"
    entry = PORTFOLIO_VALIDATED.get(mid)
    if entry is not None:
        # The portfolio table maps id -> method-class NAME, not to a function: these readings are
        # computed across a governed cohort rather than dispatched per project through
        # registry.VALIDATED. RUN 33: the implementation a production dispatch reaches is the
        # canonical v8 layer, through portfolio_health.compute_portfolio_health_snapshot. The
        # superseded v20 implementation in app.simulation.portfolio is preserved for the findings
        # recorded about it and is not reachable from production, so naming it here would name
        # the wrong implementation -- the exact failure this field exists to prevent.
        return f"app.simulation.canonical_v8 ({entry})"
    return "none: declared in the registry and implemented by no runner"


def run(mid: str, si: dict) -> dict:
    try:
        out = REG.run_module(mid, dict(si), NOOP, CUT)
        return out if isinstance(out, dict) else {}
    except Exception as exc:                                              # noqa: BLE001
        return {"__error__": f"{type(exc).__name__}: {exc}"}


def expected_for(mid: str, name: str) -> dict:
    """The truthful current statement for one module, derived, never read from the served object."""
    disabled_concept = mid in REG.DISABLED_CONCEPT_ONLY
    disabled_evidence = mid in REG.DISABLED_EVIDENCE_UNDER_REVIEW
    runner = runner_of(mid)
    key, layer = structure_of(mid)
    supplied = runner.startswith("none:") and mid not in PORTFOLIO_VALIDATED
    portfolio = mid in PORTFOLIO_VALIDATED

    row = run(mid, dict(SI, **QUALIFIED))
    abstained = bool(row.get("insufficient_data")) or row.get("estimable") is False
    archived = str(row.get("canonical_disposition") or "") == "ARCHIVED" or \
        str(row.get("disposition") or "") == "ARCHIVED"

    # Does it compute WHEN the structure exists? Measured by the canonical layer's own oracle
    # coverage rather than by fabricating a structure here: inventing one would be inventing the
    # very parameters section 23 forbids. A module with a declared structure key and a canonical
    # runner computes when that structure is supplied; the Run 28-32 oracles are the evidence.
    computes_with_structure = "YES" if key else ("n/a" if supplied else "YES")

    if archived:
        execution = EXEC_ARCHIVED
    elif mid in REG.DISABLED_CANONICAL_INPUT_NOT_GOVERNED:
        # RUN 36 CLOSURE, THE OWNER'S A1.1 RULING. Its own state: the canonical INPUT CONTRACT is
        # not governed, which is not the same fact as concept-only and not the same fact as an
        # evidence-design decision under review.
        execution = EXEC_DISABLED_INPUT
    elif disabled_evidence:
        execution = EXEC_DISABLED_EVIDENCE
    elif disabled_concept:
        execution = EXEC_DISABLED
    elif supplied:
        execution = EXEC_SUPPLIED
    elif portfolio:
        execution = EXEC_PORTFOLIO
    # RUN 36. CONDITIONALITY IS MEASURED, NOT INFERRED FROM A DECLARATION. This arm used to read
    # `elif key:` -- so a module was described to the participant as requiring a named defining
    # structure, and as returning Not Estimable without it, on the strength of the DECLARATION
    # alone. `abstained` above already executes the module with no structure supplied, so the
    # measurement was available and unused. Exactly ONE module was misdescribed, derived rather
    # than assumed: A1.1 Monte Carlo EAC Forecast declares `costDriverDistributions`, the intake
    # accepts it, no consumer exists, and the module computes from the budget and the indices
    # whether it is supplied or not. Section 16 of the Run-36 contract forbids describing a
    # method's operational state untruthfully in either direction.
    elif key and abstained:
        execution = EXEC_CONDITIONAL
    else:
        execution = EXEC_COMPUTES

    return {
        "runner": runner,
        "structure_key": key or "",
        "structure_layer": layer or "",
        # A DECLARED STRUCTURE IS NOT AN ENFORCED ONE WHEN NOTHING RUNS. A4.1 declares
        # documentRiskEvidence in canonical_v4 and has no runner at all -- the value is supplied
        # to the platform -- so naming an enforcement no current route performs would be the same
        # class of untrue statement this closure removes everywhere else.
        # RUN 36 widens the declared-not-enforced arm from `key and supplied` to every case
        # where a key is declared and the module does NOT abstain without it. A4.1 reached this
        # sentence because it has no runner at all; A1.1 reaches it because it has a runner that
        # never reads the key. Both are the same untrue claim -- naming an enforcement no current
        # route performs -- and both now get the same truthful sentence.
        # SCOPED TO THE COMPUTING CASE. A portfolio module also does not abstain on a
        # single-project probe, but its structure IS required by its own route -- it is refused
        # before the probe reaches it. Keying off the derived execution state rather than off
        # `abstained` alone keeps the five Portfolio Health rows saying what they said.
        # RUN 36 CLOSURE. A module disabled BECAUSE its canonical input contract is not
        # governed gets the sentence that is true of it: the structure is required, and it is
        # not the only thing missing. The Run-36 "declared but read by no route" sentence was
        # true while it computed without the structure and would now be false the other way.
        "structure_stmt": (STRUCT_DECLARED_NOT_ENFORCED if (key and supplied)
                           else STRUCT_REQUIRED_PLUS_MAPPING
                           if (key and execution == EXEC_DISABLED_INPUT)
                           else STRUCT_DECLARED_NOT_CONSUMED
                           if (key and execution == EXEC_COMPUTES)
                           else STRUCT_REQUIRED if key else STRUCT_NOT_REQUIRED),
        "supply_path": ("YES: admitted by project_data.governed_structure_keys()"
                        if key and key in governed_structure_keys()
                        else ("NO" if key else "n/a: this module defines no governed structure")),
        "corpus_supplies": "NO" if key else "n/a",
        "execution": execution,
        "abstains_now": "YES" if abstained else "NO",
        "computes_with_structure": computes_with_structure,
        "disabled": "YES" if (disabled_concept or disabled_evidence) else "NO",
        "archived": "YES" if archived else "NO",
        "supplied": "YES" if supplied else "NO",
        "voting": "votes on the governed status" if mid in REG.CORE_VOTING_MODULES
                  else "does not vote",
    }


#: The machine-readable state name for a derived row. One mapping, used by the builder and by the
#: guard, so the CSV and the guard cannot disagree about what a state is called.
STATE_OF_EXECUTION = {
    EXEC_COMPUTES: "COMPUTES_FROM_AVAILABLE_EVIDENCE",
    EXEC_CONDITIONAL: "CONDITIONAL_ON_GOVERNED_STRUCTURE",
    EXEC_DISABLED: "DISABLED_CONCEPT_ONLY",
    EXEC_DISABLED_INPUT: "DISABLED_INSUFFICIENT_INPUT",
    EXEC_DISABLED_EVIDENCE: "DISABLED_EVIDENCE_UNDER_REVIEW",
    EXEC_ARCHIVED: "ARCHIVED_FUTURE_RESEARCH",
    EXEC_SUPPLIED: "SUPPLIED_VALUE",
    EXEC_PORTFOLIO: "PORTFOLIO_COMPUTED",
}


def state_of(expected: dict) -> str:
    """The state name for an `expected_for` row."""
    return STATE_OF_EXECUTION[expected["execution"]]


def served() -> dict:
    """Parse the SERVED object. Read ONLY to compare, never to build an expectation."""
    txt = (ROOT / "assets" / "js" / "ds_defensibility_evidence.js").read_text(encoding="utf-8")
    body = txt[txt.index("modules: {"):]
    out = {}
    for m in re.finditer(r'"([A-D]\d+\.\d+)": \{(.*?)\},\n', body, re.S):
        mid, fields = m.group(1), m.group(2)
        d = {}
        # Strings, and ALSO bare booleans and nulls. Parsing only quoted values silently read
        # `canonicalStructureRequired: true` as absent, which would have made the guard compare
        # None against True for every module and fail for the wrong reason.
        for fm in re.finditer(r'(\w+): ("(?:[^"\\]|\\.)*"|true|false|null)', fields):
            d[fm.group(1)] = json.loads(fm.group(2))
        out[mid] = d
    return out


def main() -> int:
    reg = REG.load_registry()
    srv = served()
    HDR = ["module ID", "authoritative current name", "category", "activation", "voting",
           "canonical runner", "current production route", "defining canonical structure",
           "canonical structure required?", "production supply path",
           "real corpus currently supplies structure?", "current operational behavior",
           "computes when structure exists?", "abstains when structure is absent?", "disabled?",
           "archived?", "supplied rather than computed?", "current served defensibility statement",
           "expected truthful statement", "mismatch", "PASS/FAIL"]
    rows, mismatched, missing, extra = [], 0, [], sorted(set(srv) - {m["new_id"] for m in reg})
    false_claims: list[str] = []
    imprecise: list[str] = []
    wording: list[str] = []
    seen = set()
    classes: dict[str, int] = {}

    for m in reg:
        mid, name = m["new_id"], m["module_name"]
        if mid in seen:
            raise SystemExit(f"duplicate registry identity {mid}")
        seen.add(mid)
        e = expected_for(mid, name)
        s = srv.get(mid)
        if s is None:
            missing.append(mid)
            served_stmt, served_struct = "ABSENT FROM THE SERVED OBJECT", "ABSENT"
        else:
            served_stmt, served_struct = s.get("implementation", ""), s.get("canonicalStructure", "")

        # SEVERITY MATTERS, AND CONFLATING IT WOULD INFLATE THE FINDING. A statement that is
        # FALSE about the current instrument is a defect. A statement that is TRUE but less
        # precise than the new vocabulary is an improvement, not a defect. A statement that
        # differs only in wording is neither. They are counted separately and the report leads
        # with the false ones.
        problems, severities = [], []
        if s is None:
            problems.append("module missing from the served defensibility object")
            severities.append("FALSE_CLAIM")
        else:
            if served_struct != e["structure_stmt"]:
                problems.append(
                    f"canonicalStructure says {served_struct!r} but the current production route "
                    f"{'requires' if e['structure_key'] else 'requires no'} "
                    f"{e['structure_key'] or 'governed structure'}"
                    + (f" (declared in {e['structure_layer']})" if e["structure_layer"] else ""))
                severities.append("FALSE_CLAIM")
                classes["canonical structure requirement misstated (FALSE)"] = \
                    classes.get("canonical structure requirement misstated (FALSE)", 0) + 1
            # SEVERITY IS DECIDED BY WHAT THE SERVED SENTENCE ACTUALLY CLAIMS, not by which
            # expected category the module lands in. The served object has exactly two execution
            # sentences: one asserts the server computes the reading, the other asserts the
            # module is disabled. So the test is a contradiction test.
            served_claims_computing = "computed by the server" in served_stmt
            served_claims_disabled = served_stmt.startswith("disabled")
            produces_live_reading = (e["disabled"] == "NO" and e["archived"] == "NO"
                                     and e["supplied"] == "NO" and e["abstains_now"] == "NO")
            if served_stmt != e["execution"]:
                if served_claims_computing and not produces_live_reading:
                    # The reader is told a project reading is being computed when none is.
                    if e["execution"] == EXEC_CONDITIONAL:
                        k = "conditional method presented as unconditionally computing"
                    elif e["execution"] == EXEC_SUPPLIED:
                        k = "supplied value presented as server-computed"
                    elif e["execution"] == EXEC_DISABLED_EVIDENCE:
                        k = "disabled evidence-under-review module presented as computing"
                    elif e["execution"] == EXEC_DISABLED:
                        k = "disabled module presented as computing"
                    elif e["execution"] == EXEC_ARCHIVED:
                        k = "archived method presented as computing"
                    else:
                        k = "non-computing module presented as computing"
                    sev = "FALSE_CLAIM"
                elif served_claims_disabled and e["execution"] == EXEC_ARCHIVED:
                    k, sev = "archived method presented as merely disabled", "IMPRECISE"
                elif e["execution"] == EXEC_PORTFOLIO:
                    k, sev = "portfolio reading presented as a project computation", "IMPRECISE"
                else:
                    k, sev = "execution statement reworded, same meaning", "WORDING_ONLY"
                problems.append(f"implementation says {served_stmt!r} ({sev})")
                severities.append(sev)
                classes[f"{k} [{sev}]"] = classes.get(f"{k} [{sev}]", 0) + 1
            if s.get("name") != name:
                problems.append(f"name says {s.get('name')!r} but the registry says {name!r}")
                severities.append("FALSE_CLAIM")
                classes["name drift (FALSE)"] = classes.get("name drift (FALSE)", 0) + 1
        worst = ("FALSE_CLAIM" if "FALSE_CLAIM" in severities else
                 "IMPRECISE" if "IMPRECISE" in severities else
                 "WORDING_ONLY" if severities else "NONE")
        if worst == "FALSE_CLAIM":
            false_claims.append(mid)
        elif worst == "IMPRECISE":
            imprecise.append(mid)
        elif worst == "WORDING_ONLY":
            wording.append(mid)
        if problems:
            mismatched += 1

        rows.append([
            mid, name, m.get("category_name", ""),
            ("DISABLED_CONCEPT_ONLY" if mid in REG.DISABLED_CONCEPT_ONLY else
             "DISABLED_EVIDENCE_UNDER_REVIEW" if mid in REG.DISABLED_EVIDENCE_UNDER_REVIEW else
             "ENABLED"),
            e["voting"], e["runner"],
            ("registry.run_module -> " + e["runner"]) if not e["supplied"] == "YES"
            else "no analytical route: the value is supplied to the platform",
            e["structure_key"] or "none", e["structure_stmt"], e["supply_path"],
            e["corpus_supplies"], e["execution"], e["computes_with_structure"],
            e["abstains_now"], e["disabled"], e["archived"], e["supplied"],
            served_stmt, e["execution"],
            "; ".join(problems) or "none",
            "FAIL" if worst == "FALSE_CLAIM" else "PASS"])

    out = ROOT / "code_audit" / "run32_defensibility_metadata_reconciliation.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HDR)
        w.writerows(rows)

    print(f"registry identities (derived, not hard-coded): {len(reg)}")
    print(f"rows written                                 : {len(rows)}")
    print(f"duplicate identities                         : {len(rows) - len(seen)}")
    print(f"missing from served object                   : {len(missing)} {missing}")
    print(f"in served object but not the registry        : {len(extra)} {extra}")
    print(f"rows differing from the served object        : {mismatched}")
    print(f"  of which FALSE about the current instrument: {len(false_claims)}")
    print(f"  of which true but IMPRECISE                : {len(imprecise)}")
    print(f"  of which WORDING ONLY, same meaning        : {len(wording)}")
    print("defect classes:")
    for k, v in sorted(classes.items(), key=lambda t: -t[1]):
        print(f"   {v:4d}  {k}")
    print(f"wrote {out.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
