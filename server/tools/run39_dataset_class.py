#!/usr/bin/env python3
"""
Run 39: the governed dataset-classification layer.

WHY THIS EXISTS AND WHAT IT DELIBERATELY IS NOT
-----------------------------------------------
Run 38's frozen analysis export carries a `record_class` column whose value is derived from a
PSEUDONYMOUS-CODE PREFIX (`run38_analysis_export.TEST_ONLY_CODE_PREFIX`). That is a naming
convention. Run 39's controlling specification forbids inferring dataset class from a
participant name or a date, so the prefix CANNOT be the authority for whether an observation
belongs to the main study.

Run 39 therefore does NOT change the frozen export. `record_class`, the 58 columns, the
categorical levels and the derivations of `og-analysis-2026.08-v1` are untouched, and this
module never writes into them. Instead it adds the OPERATIONAL PROVENANCE LAYER the
specification asks for: an explicit, governed, human-maintained registry that names each study
participant's dataset class as DATA, separately from anything the participant is called.

FAIL-CLOSED IS THE WHOLE POINT
------------------------------
A participant who is not in the registry is `UNCLASSIFIED`. UNCLASSIFIED is not a dataset class;
it is the absence of one, and it can never be exported as MAIN_STUDY. Adding a participant to
the main study is therefore an explicit, auditable, reviewable act. Forgetting to classify
someone excludes them; it never silently includes them. The opposite default would mean that the
day someone creates an account by accident, their rows join the primary dataset.

WHAT THIS LAYER CANNOT DO
-------------------------
It is a governance control, not a technical one. It governs what the EXPORT emits. It does not
and cannot prevent someone with direct database access from writing rows. Section 6 of the
Run-39 specification asks that question separately and it is answered separately, in
`code_audit/run39_administrative_authority_boundary.csv`, without claiming technical
immutability where only operational access control exists.
"""
from __future__ import annotations

import csv
import hashlib
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
REGISTRY = REPO / "research" / "study_execution" / "dataset_class_registry.csv"

#: CLOSED VOCABULARY. A value outside this set is a hard error, never a new class.
DATASET_CLASSES: tuple[str, ...] = ("TEST_ONLY", "PILOT", "MAIN_STUDY")

#: The fail-closed sentinel for a participant the registry does not name. It is NOT a member of
#: DATASET_CLASSES, deliberately: it is the absence of a classification, not a third kind of data.
UNCLASSIFIED = "UNCLASSIFIED"

#: Only this class may be exported as the primary study dataset.
MAIN_STUDY = "MAIN_STUDY"

REGISTRY_COLUMNS: tuple[str, ...] = (
    "study_participant_id",
    "dataset_class",
    "registered_on",
    "registering_authority",
    "note",
)


class RegistryError(RuntimeError):
    """Raised when the registry itself is malformed. Never silently tolerated."""


def load_registry(path: pathlib.Path | None = None) -> dict[str, str]:
    """
    The registry as {study_participant_id: dataset_class}.

    A malformed registry RAISES rather than degrading to an empty mapping. An empty mapping
    would silently classify every participant UNCLASSIFIED, which looks safe (nothing exports)
    but hides the real fault, and a later reader would not be able to tell "nobody is registered"
    from "the file is broken".
    """
    path = path or REGISTRY
    if not path.exists():
        raise RegistryError(f"dataset class registry is missing: {path}")

    mapping: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None or tuple(reader.fieldnames) != REGISTRY_COLUMNS:
            raise RegistryError(
                f"registry columns are {reader.fieldnames}, expected {list(REGISTRY_COLUMNS)}")
        for line, row in enumerate(reader, start=2):
            pid = (row.get("study_participant_id") or "").strip()
            cls = (row.get("dataset_class") or "").strip()
            if not pid:
                raise RegistryError(f"registry line {line}: empty study_participant_id")
            if cls not in DATASET_CLASSES:
                raise RegistryError(
                    f"registry line {line}: dataset_class {cls!r} is not one of "
                    f"{list(DATASET_CLASSES)}. The vocabulary is closed; a value that fits none "
                    f"of it is a governance error, not a new class.")
            if pid in mapping and mapping[pid] != cls:
                raise RegistryError(
                    f"registry line {line}: {pid} is registered twice with conflicting classes "
                    f"({mapping[pid]} and {cls}). A participant has exactly one dataset class.")
            mapping[pid] = cls
    return mapping


def classify(study_participant_id: str | None,
             registry: dict[str, str] | None = None) -> str:
    """
    THE ONLY GOVERNED ANSWER to 'which dataset does this observation belong to'.

    It reads the registry and nothing else. It does not look at the participant's code prefix,
    its display label, its creation date, or any property of the row. That is the requirement:
    changing what a participant is CALLED must not change which dataset they are IN.
    """
    reg = load_registry() if registry is None else registry
    return reg.get((study_participant_id or "").strip(), UNCLASSIFIED)


def eligible_for_main_study(study_participant_id: str | None,
                            registry: dict[str, str] | None = None) -> bool:
    """Fail-closed: only an explicit MAIN_STUDY registration qualifies."""
    return classify(study_participant_id, registry) == MAIN_STUDY


def partition(rows: list[dict], registry: dict[str, str] | None = None) -> dict[str, list[dict]]:
    """Split analysis rows by governed class. Keys include UNCLASSIFIED."""
    reg = load_registry() if registry is None else registry
    out: dict[str, list[dict]] = {c: [] for c in DATASET_CLASSES}
    out[UNCLASSIFIED] = []
    for r in rows:
        out[classify(r.get("study_participant_id"), reg)].append(r)
    return out


def select(rows: list[dict], dataset_class: str,
           registry: dict[str, str] | None = None) -> list[dict]:
    """Rows of exactly one governed class. Refuses UNCLASSIFIED as an export target."""
    if dataset_class not in DATASET_CLASSES:
        raise RegistryError(
            f"{dataset_class!r} is not an exportable dataset class; permitted: "
            f"{list(DATASET_CLASSES)}")
    reg = load_registry() if registry is None else registry
    return [r for r in rows if classify(r.get("study_participant_id"), reg) == dataset_class]


def registry_digest(path: pathlib.Path | None = None) -> str:
    """sha256 over the registry bytes, so a launch manifest can pin which registry it saw."""
    path = path or REGISTRY
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    reg = load_registry()
    counts: dict[str, int] = {}
    for cls in reg.values():
        counts[cls] = counts.get(cls, 0) + 1
    print(f"registry: {REGISTRY.relative_to(REPO)}")
    print(f"digest:   {registry_digest()}")
    for cls in DATASET_CLASSES:
        print(f"  {cls:12s} {counts.get(cls, 0)}")
    print(f"  (unregistered participants classify as {UNCLASSIFIED} and can never be "
          f"exported as {MAIN_STUDY})")
    sys.exit(0)
