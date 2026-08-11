"""Test-only, read-only importer for the staged synthetic research fixtures.

Rules this module enforces, and the reasons they exist:

* It reads ONLY from research_fixtures/synthetic/OG-SYNTH-0.2. There is no code path here
  that reads a production database, a production asset, or the network, and no code path
  that writes anything anywhere. A missing or malformed fixture raises; it never falls back
  to production data.
* Every loaded row is frozen. Records are tuples of (key, value) behind a mapping that
  refuses assignment, so a test cannot mutate a fixture and then assert on its own edit.
* Every row must carry data_origin == "SYNTHETIC_RESEARCH_FIXTURE" and
  not_for_empirical_validation == true. A row failing either is rejected, loudly.
* Provenance (package, programme version, package version, generator, seed) travels with
  every table so a test result can never be reported without saying what produced it.
* Module resolution goes through the authoritative alias tables plus the versioned Run 9
  overlay, by identifier. Name-only matching is not offered by this module at all.

Nothing loaded through this importer activates a module, makes a module voting, validates a
status band, or constitutes empirical validation of anything.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

SYNTHETIC_ORIGIN = "SYNTHETIC_RESEARCH_FIXTURE"

REPO_ROOT = Path(__file__).resolve().parents[4]
FIXTURE_ROOT = REPO_ROOT / "research_fixtures" / "synthetic"
PACKAGE_ROOT = (
    FIXTURE_ROOT / "OG-SYNTH-0.2" / "Opus_Gubernatio_Synthetic_Programme_v0.2"
)
OVERLAY_PATH = FIXTURE_ROOT / "module_id_aliases_overlay.csv"

PACKAGE_A = "package_A_project_structures"
PACKAGE_B = "package_B_reference_training_decisions"
PACKAGE_C = "package_C_optional_activation_lab"


class FixtureError(RuntimeError):
    """Any refusal by this layer: bad path, bad origin, bad key, bad package."""


class FrozenRecord(Mapping):
    """An immutable mapping. Assignment and deletion raise."""

    __slots__ = ("_data",)

    def __init__(self, data: Mapping[str, Any]):
        object.__setattr__(self, "_data", dict(data))

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __setitem__(self, *_a: Any) -> None:
        raise FixtureError("synthetic fixture records are read-only")

    def __delitem__(self, *_a: Any) -> None:
        raise FixtureError("synthetic fixture records are read-only")

    def __setattr__(self, *_a: Any) -> None:
        raise FixtureError("synthetic fixture records are read-only")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"FrozenRecord({self._data!r})"


class FixtureTable:
    """A frozen table plus the provenance of the rows in it."""

    __slots__ = ("relpath", "rows", "provenance")

    def __init__(self, relpath: str, rows: Sequence[FrozenRecord], provenance: FrozenRecord):
        object.__setattr__(self, "relpath", relpath)
        object.__setattr__(self, "rows", tuple(rows))
        object.__setattr__(self, "provenance", provenance)

    def __setattr__(self, *_a: Any) -> None:
        raise FixtureError("synthetic fixture tables are read-only")

    def __len__(self) -> int:
        return len(self.rows)

    def __iter__(self) -> Iterator[FrozenRecord]:
        return iter(self.rows)


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _resolve(relpath: str) -> Path:
    """Resolve inside the staged package and nowhere else."""
    path = (PACKAGE_ROOT / relpath).resolve()
    if not str(path).startswith(str(PACKAGE_ROOT.resolve())):
        raise FixtureError(f"refusing to read outside the synthetic package: {relpath}")
    if not path.exists():
        raise FixtureError(f"missing synthetic asset: {relpath}")
    return path


def _check_origin(row: Mapping[str, Any], relpath: str, index: int) -> None:
    origin = row.get("data_origin")
    if origin != SYNTHETIC_ORIGIN:
        raise FixtureError(
            f"{relpath} row {index}: data_origin is {origin!r}, "
            f"not {SYNTHETIC_ORIGIN!r}"
        )
    flag = row.get("not_for_empirical_validation")
    if not _truthy(flag):
        raise FixtureError(
            f"{relpath} row {index}: not_for_empirical_validation is {flag!r}, not true"
        )


def load_table(
    relpath: str,
    *,
    primary_key: Sequence[str] | None = None,
    expect_package: str | None = None,
) -> FixtureTable:
    """Load one CSV from the staged package as a frozen table.

    primary_key, when given, is enforced: missing components and duplicates raise.
    expect_package, when given, asserts the file really sits in that package directory.
    """
    if expect_package is not None and not relpath.startswith(expect_package + "/"):
        raise FixtureError(
            f"{relpath} is not in package {expect_package}; refusing the load"
        )
    path = _resolve(relpath)
    rows: list[FrozenRecord] = []
    seen: set[tuple] = set()
    provenance: dict[str, Any] = {}
    with path.open(newline="", encoding="utf-8") as fh:
        for index, raw in enumerate(csv.DictReader(fh), start=1):
            _check_origin(raw, relpath, index)
            if primary_key:
                key = tuple(raw.get(col) for col in primary_key)
                if any(component in (None, "") for component in key):
                    raise FixtureError(
                        f"{relpath} row {index}: incomplete primary key {primary_key}"
                    )
                if key in seen:
                    raise FixtureError(
                        f"{relpath} row {index}: duplicate primary key {key}"
                    )
                seen.add(key)
            if not provenance:
                provenance = {
                    "programme_version": raw.get("programme_version"),
                    "package_version": raw.get("package_version"),
                    "generator_version": raw.get("generator_version"),
                    "random_seed": raw.get("random_seed"),
                    "data_origin": raw.get("data_origin"),
                    "not_for_empirical_validation": True,
                    "relpath": relpath,
                }
            rows.append(FrozenRecord(raw))
    if not rows:
        raise FixtureError(f"{relpath}: no rows")
    return FixtureTable(relpath, rows, FrozenRecord(provenance))


def load_json(relpath: str) -> Mapping[str, Any]:
    """Load a JSON asset, enforcing the same origin contract at the document level."""
    path = _resolve(relpath)
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("data_origin") != SYNTHETIC_ORIGIN:
        raise FixtureError(
            f"{relpath}: data_origin is {doc.get('data_origin')!r}, not {SYNTHETIC_ORIGIN!r}"
        )
    if not _truthy(doc.get("not_for_empirical_validation")):
        raise FixtureError(f"{relpath}: not_for_empirical_validation is not true")
    return FrozenRecord(doc)


def check_foreign_key(
    child: FixtureTable,
    child_cols: Sequence[str],
    parent: FixtureTable,
    parent_cols: Sequence[str],
) -> list[str]:
    """Return the list of child keys with no parent row. Empty list means clean."""
    parent_keys = {tuple(row[c] for c in parent_cols) for row in parent}
    orphans = []
    for row in child:
        key = tuple(row[c] for c in child_cols)
        if key not in parent_keys:
            orphans.append(f"{child.relpath}:{key}")
    return orphans


# --------------------------------------------------------------- module resolution

def load_module_aliases() -> tuple[FixtureTable, FixtureTable]:
    """The package's own authoritative alias table and asset map."""
    return (
        load_table("module_id_aliases.csv"),
        load_table("module_asset_map.csv"),
    )


def load_alias_overlay() -> tuple[FrozenRecord, ...]:
    """The versioned Run 9 overlay. It adds identifiers; it never edits the package."""
    if not OVERLAY_PATH.exists():
        raise FixtureError("missing module_id_aliases_overlay.csv")
    with OVERLAY_PATH.open(newline="", encoding="utf-8") as fh:
        return tuple(FrozenRecord(row) for row in csv.DictReader(fh))


def resolve_modules() -> dict[str, FrozenRecord]:
    """repository module id -> {synthetic id, name, category, files, source}.

    Built from the package alias table, the package asset map and the Run 9 overlay, by
    identifier only. No name matching happens anywhere in this function.
    """
    aliases, asset_map = load_module_aliases()
    files_by_synthetic_id = {row["module_id"]: row["primary_files"] for row in asset_map}
    resolved: dict[str, FrozenRecord] = {}
    for row in aliases:
        repo_id = row["code_module_id"]
        if repo_id in resolved:
            raise FixtureError(f"duplicate repository module id in alias table: {repo_id}")
        resolved[repo_id] = FrozenRecord(
            {
                "repository_module_id": repo_id,
                "synthetic_module_id": row["literature_module_id"],
                "module_name": row["module_name"],
                "category_number": row["category_number"],
                "category_name": row["category_name"],
                "synthetic_package": row["synthetic_package"],
                "primary_files": files_by_synthetic_id.get(row["literature_module_id"], ""),
                "source": "package_module_id_aliases",
            }
        )
    for row in load_alias_overlay():
        repo_id = row["repository_module_id"]
        if repo_id in resolved:
            raise FixtureError(f"overlay collides with the package alias table: {repo_id}")
        synthetic_ids = {r["synthetic_module_id"] for r in resolved.values()}
        if row["synthetic_module_id"] in synthetic_ids:
            raise FixtureError(
                f"overlay reuses a synthetic module id: {row['synthetic_module_id']}"
            )
        resolved[repo_id] = FrozenRecord(
            {
                "repository_module_id": repo_id,
                "synthetic_module_id": row["synthetic_module_id"],
                "module_name": row["module_name"],
                "category_number": row["category_number"],
                "category_name": row["category_name"],
                "synthetic_package": "overlay",
                "primary_files": row["primary_files"],
                "source": row["source"],
            }
        )
    return resolved


def locate_asset(name: str) -> str:
    """Find one staged asset by relative path or by basename, and return its relpath.

    The package asset map lists bare file names; the overlay lists relative paths. Both are
    resolved here against the files that actually exist on disk, so a mapping that names a
    file the package does not contain fails rather than passing on the map's word.
    """
    direct = PACKAGE_ROOT / name
    if direct.exists():
        return name
    matches = [
        p.relative_to(PACKAGE_ROOT).as_posix()
        for p in PACKAGE_ROOT.rglob(Path(name).name)
        if p.is_file() and "generators" not in p.parts
    ]
    if not matches:
        raise FixtureError(f"no staged asset named {name}")
    if len(matches) > 1:
        raise FixtureError(f"ambiguous asset name {name}: {matches}")
    return matches[0]


def module_assets(repository_module_id: str) -> tuple[str, ...]:
    """The staged files a repository module id resolves to, by identifier."""
    resolved = resolve_modules()
    if repository_module_id not in resolved:
        raise FixtureError(f"no automatic join for module id {repository_module_id}")
    files = resolved[repository_module_id]["primary_files"]
    return tuple(locate_asset(f) for f in files.split("|") if f)
