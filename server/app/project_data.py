"""
THE GOVERNED PROJECT DATA OBJECT: the intake path for the canonical v3 structures.

WHY THIS FILE EXISTS. Run 28 built `server/app/simulation/canonical_v3.py`, which defines
twenty-three canonical structures and computes only from them. Twenty of the twenty-eight
Category 1 to 3 modules abstain on the real corpus because their defining structure is absent.
That abstention is scientifically correct ONLY IF the platform has a real way to RECEIVE the
structure. Run 28's closure audit found that only two of the twenty-three structures were ever
written by production code -- `milestoneForecastHistory` and `costRiskModel`, both assembled in
`documents.py` -- and every other structure appeared in TEST FIXTURES AND NOWHERE ELSE. A
structure that only a test can supply is not a supply path; it is a description of one.

WHAT THIS FILE IS. A governed, append-only, period-effective store for structured project data
that the analytical layer reads, reachable from the same `/exec` API surface every other write
uses, through the `saveprojectdata` action in `writes.py`. It is the concrete repository object
the supply-path closure table names for every structure whose values cannot be read out of a
reporting-period document.

THE FIVE RULES IT ENFORCES, each of them a defect this programme has already found in another
form.

1. THE STRUCTURE KEY MUST BE ONE THE ANALYTICAL LAYER ACTUALLY READS. The vocabulary is read
   from `canonical_v3.V3_STRUCTURE_KEYS`, never duplicated here, so a caller cannot write a key
   no computation consumes and have it sit in the record forever looking like data. This is the
   same rule `w_overwritesignal` applies to scalar fields through `field_registry`.

2. NOTHING IS VALIDATED FOR PLAUSIBILITY HERE AND NO VALUE IS EVER SUPPLIED. The record is
   stored as the caller gave it. Whether it satisfies the canonical method's contract is decided
   by `canonical_v3`'s own guards at computation time, which refuse an incomplete or
   provenance-less structure by raising `StructureAbsent`. Two validators would drift; one
   validator, in the place that defines the contract, cannot.

3. IT IS PERIOD-EFFECTIVE, SO AN EARLIER PERIOD RECOMPUTES BYTE-IDENTICALLY. Every revision
   carries the reporting period from which it takes effect. A computation of period N sees the
   latest revision whose effective period is at or below N and nothing later. Supplying data
   today therefore cannot silently change a result stored for an earlier period, which is the
   acceptance condition `test_schedule_milestones.py` already asserts for the document path.

4. IT IS APPEND-ONLY. A correction is a new revision, never an edit of an old one, so the record
   of what the modules were given at the moment of a decision survives the correction.

5. A DOCUMENT-DERIVED STRUCTURE ALWAYS WINS. `apply_to_signal_inputs` never overwrites a key the
   period's own documents already produced. Evidence read from the project's documents outranks
   evidence typed into a form, and the merge order says so rather than depending on call order.
"""

from __future__ import annotations

from typing import Any

def governed_structure_keys() -> set[str]:
    """
    The keys a caller may supply, read from the analytical layer rather than restated.

    BOTH structure maps, not only the v3 one. The Run-28 closure audit found A2.2 Line of Balance
    and A2.3 CCPM Buffer Health in exactly the condition the twenty abstaining modules are in --
    canonical arithmetic, a declared structure key, and no production code anywhere that writes
    it -- and they are not among Run 28's twenty because Run 28 counted them as already canonical
    rather than as abstaining. Their structures are governed by `canonical.py` instead of
    `canonical_v3.py`, so reading only the v3 map would have built an intake path that could not
    reach them and left the same defect standing under a different file name.

    RUN 29 ADDS THE v4 MAP for the same reason. The eighteen Category-4 and Category-5 structures
    supplied by Run 29 are governed by `canonical_v4.py`, and reading only the earlier two maps
    would have built an intake path that could not reach a single one of them, leaving eighteen
    structures that only a test could supply. That is the exact defect Run 28's closure found and
    the exact defect section 15 of Run 29's contract forbids repeating, so the vocabulary is the
    union of all three maps and nothing here restates a key.
    """
    from .simulation.canonical import CANONICAL_STRUCTURE_KEYS
    from .simulation.canonical_v3 import V3_STRUCTURE_KEYS
    from .simulation.canonical_v4 import V4_STRUCTURE_KEYS
    return (set(V3_STRUCTURE_KEYS.values()) | set(CANONICAL_STRUCTURE_KEYS.values())
            | set(V4_STRUCTURE_KEYS.values()))


#: The document path assembles these two itself, from evidence the corpus already holds. They
#: are still accepted here -- a project whose documents do not carry a schedule may supply a
#: milestone history directly -- but rule 5 means the document-derived one wins where both exist.
DOCUMENT_ASSEMBLED = ("milestoneForecastHistory", "costRiskModel")


class ProjectDataError(ValueError):
    """A supplied project data record that this store refuses to hold."""


def revisions(project_doc: dict | None) -> dict[str, list[dict]]:
    """The stored revisions, structure key -> list of revision envelopes, oldest first."""
    store = (project_doc or {}).get("projectData")
    if not isinstance(store, dict):
        return {}
    out: dict[str, list[dict]] = {}
    for key, entries in store.items():
        if isinstance(entries, list):
            out[str(key)] = [e for e in entries if isinstance(e, dict)]
    return out


def add_revision(project_doc: dict, structure: str, record: dict, *,
                 effective_period: int, supplied_by: str, source: str,
                 at: str) -> dict:
    """
    Returns a NEW project document carrying one further revision. Refuses, rather than
    normalising, anything it cannot hold: an unknown structure key, a record that is not an
    object, a period that is not a positive whole number, or a blank provenance.
    """
    known = governed_structure_keys()
    if structure not in known:
        raise ProjectDataError(
            f"Unknown project data structure: {structure!r}. This platform has no analytical "
            f"structure by that name; nothing was stored.")
    if not isinstance(record, dict) or not record:
        raise ProjectDataError(
            "A project data record must be an object carrying the structure's own fields; "
            "nothing was stored.")
    try:
        period = int(effective_period)
    except (TypeError, ValueError):
        raise ProjectDataError("The reporting period this record takes effect from must be a "
                               "whole number; nothing was stored.") from None
    if period < 1:
        raise ProjectDataError("The reporting period this record takes effect from must be one "
                               "or greater; nothing was stored.")
    if not str(supplied_by or "").strip() or not str(source or "").strip():
        raise ProjectDataError(
            "A project data record must say who supplied it and where the figures came from, "
            "because the analytical layer carries that provenance back out with the result; "
            "nothing was stored.")
    fresh = dict(project_doc or {})
    store = {k: list(v) for k, v in revisions(fresh).items()}
    store.setdefault(structure, []).append({
        "revision": len(store.get(structure, [])) + 1,
        "effective_period": period,
        "supplied_by": str(supplied_by).strip(),
        "source": str(source).strip(),
        "at": at,
        "record": record,
    })
    fresh["projectData"] = store
    return fresh


def structures_as_of(project_doc: dict | None, period: int) -> dict[str, dict]:
    """
    The structures in force for a computation of `period`: for each key, the record of the
    LATEST revision whose effective period is at or below it. A structure supplied only for a
    later period is not visible here, so recomputing an earlier period reproduces it exactly.
    """
    out: dict[str, dict] = {}
    for key, entries in revisions(project_doc).items():
        applicable = [e for e in entries
                      if isinstance(e.get("effective_period"), int)
                      and e["effective_period"] <= int(period)]
        if not applicable:
            continue
        chosen = max(applicable, key=lambda e: (e["effective_period"],
                                                e.get("revision") or 0))
        record = chosen.get("record")
        if isinstance(record, dict) and record:
            out[key] = record
    return out


def apply_to_signal_inputs(si: dict, project_doc: dict | None, period: int) -> list[str]:
    """
    Merges the in-force structures onto the signal inputs the modules are given, WITHOUT
    overwriting anything the period's own documents produced, and returns the keys it added so
    the caller can record them. Mutates `si`, which is the dict stored on the result row, so the
    stored record shows exactly what the modules saw.
    """
    added = []
    for key, record in sorted(structures_as_of(project_doc, period).items()):
        if key in si:
            continue
        si[key] = record
        added.append(key)
    return added
