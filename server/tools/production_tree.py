"""
RUN 22 ITEM 5. THE PRODUCTION SURFACE, DISCOVERED FROM THE TREE RATHER THAN ENUMERATED.

THE DEFECT THIS REPLACES, STATED AS IT WAS FOUND. Every freeze this programme has taken so far
-- run18_production_baseline.sha256, run20_production_baseline.sha256 and the immovable
run20_production_freeze.sha256 -- is a list of 143 named paths. The guard in
test_run20_declared_production_changes.py reads that list, checks that every file IN it still
exists and still hashes as recorded, and then stops. A production file that is not in the list
is not merely unchecked: it is invisible. The guard cannot report its absence because the guard
never asks the tree what is there.

THIS IS NOT HYPOTHETICAL AND RUN 22 MEASURED IT. Walking the deployed roots at the Run-22
starting commit ba5bfaf and subtracting the 143 names leaves, among other files, FIVE live
backend Python modules totalling about 2,240 lines:

    server/app/simulation/lineage.py            907 lines, imported by research_export, writes,
                                                fusion, compute and the registry
    server/app/simulation/method_labels.py      426 lines, imported by the registry
    server/app/simulation/parameters.py         412 lines, imported by models_sim and the registry
    server/app/simulation/qualification_gate.py 335 lines, imported by compute
    server/app/simulation/arm_lineage.py        162 lines, imported by models_evc and models_gov

That is the whole Category-9 lineage layer and the qualification gate -- the code Run 20 spent
twelve cycles qualifying -- sitting outside every freeze the programme has taken. Also outside
it: logo.png and research/deepdive.html, both served by name from app.main, and every vendored
font and the country geojson under assets/vendor, all of which app.main mounts wholesale.

HOW THIS FILE IS DIFFERENT. It does not hold a list of files. It holds a list of ROOTS and a
list of EXCLUSIONS, and it walks. The names come out of the filesystem, so a file added to a
production root appears in the inventory the moment it exists, whether or not anyone remembered
to declare it, and whether or not git is tracking it. The pinned manifest is then the RECORD of
what the walk found at freeze time; it is the expected value, never the source of the names.
The distinction is the entire point of the item: discovery is dynamic, the reference is pinned.

WHY UNTRACKED FILES COUNT. app.main mounts `assets/` with StaticFiles, which serves whatever is
in the directory. An untracked file dropped into assets/js is served to a participant exactly
like a tracked one. A freeze built from `git ls-files` would not see it. The walk uses the
filesystem for that reason and reports tracked state as an attribute rather than as a filter.

THE ROOTS ARE THE DEPLOYED SURFACE, DERIVED FROM app.main AND render.yaml, NOT CHOSEN BY TASTE.
render.yaml starts `uvicorn app.main:app` with rootDir server. app.main serves index.html,
logo.png and research/deepdive.html by name and mounts assets/ as a directory. The backend is
server/app. The migrations that shape the production database are server/alembic. Its pinned
dependency set is server/requirements.txt. Those, plus the contract baseline the Run-20 freeze
already protected, are the roots.
"""

from __future__ import annotations

import hashlib
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]

#: (path, recursive, why). A recursive root is walked to any depth; a non-recursive entry is a
#: single file. Every entry is justified by the deployment surface, not by convention.
PRODUCTION_ROOTS: tuple[tuple[str, bool, str], ...] = (
    ("index.html", False,
     "the served application entry document; app.main returns it by name from REPO_ROOT"),
    ("logo.png", False,
     "served by name from app.main as _LOGO_PNG. NOT in the 143-file freeze"),
    ("research/deepdive.html", False,
     "served by name from app.main as _DEEPDIVE_HTML, the researcher-facing surface Run 21 "
     "corrected the four withdrawn regulatory claims on. NOT in the 143-file freeze"),
    ("assets", True,
     "app.main mounts this WHOLE DIRECTORY with StaticFiles, so every file beneath it is served "
     "to a participant, including the vendored fonts and geojson the 143-file freeze omitted"),
    ("server/app", True,
     "the backend uvicorn runs. Contains the analytical engine, the registry, the lineage layer "
     "and the qualification gate"),
    ("server/alembic", True,
     "the migrations that define the production database schema; a changed migration changes "
     "production data structure even though no request touches the file"),
    ("server/requirements.txt", False,
     "the pinned dependency set render.yaml installs; a change here changes the running code "
     "without changing a single repository source line"),
    ("server/alembic.ini", False, "migration configuration read at deploy time"),
    ("render.yaml", False,
     "the deployment blueprint: service, root directory, build and start commands"),
    ("p0-baseline/contracts", True,
     "the frozen API contract baseline the Run-20 freeze already protected; kept in scope so "
     "this inventory is a superset of the manifest it replaces"),
    ("p0-baseline/live", True, "the captured live contract responses, as above"),
    ("p0-baseline/reconciliation", True, "the contract reconciliation record, as above"),
    ("p0-baseline/MODULE_TAXONOMY.md", False, "the frozen module taxonomy, in the Run-20 freeze"),
    ("p0-baseline/module_renumbering_map.csv", False,
     "in the Run-20 freeze. NOTE the standing programme rule: its old_id column is NOT canonical "
     "identity. It is frozen because it is read, not because it is authoritative"),
)

#: THE SCIENTIFIC AUTHORITY, WALKED THE SAME WAY AND FOR THE SAME REASON. The supervisory
#: specification is the controlling theory: its own metadata says the repository source code is
#: the object under test and never a source of theory. Its SHA-256 is quoted in four reports, in
#: T6_HANDOFF.md and in its own metadata file -- and until Run 22 NOTHING EXECUTABLE CHECKED IT.
#: A hash that appears only in prose is a claim, not a guard. These roots are walked and pinned
#: exactly as the production roots are, so a silent edit to the controlling specification, or a
#: new methodology document nobody declared, is detected rather than described.
AUTHORITY_ROOTS: tuple[tuple[str, bool, str], ...] = (
    ("research/methodology", True,
     "the controlling supervisory method specification and its metadata record. CONTROLLING "
     "status: where this and the implementation disagree, this governs what the method ought "
     "to be"),
    (".gitattributes", False,
     "carries the `-text` rule that stops any checkout filter rewriting the specification's line "
     "endings. If this file changes, the specification's bytes can change without the "
     "specification being edited, so it is authority-critical in its own right"),
)

#: (glob suffix or directory name, why). Applied to the walk. Each exclusion must name a reason
#: that is about the FILE not being production, never about the file being inconvenient.
EXCLUSIONS: tuple[tuple[str, str], ...] = (
    ("__pycache__", "CPython bytecode cache. Generated from the .py files already in the "
                    "inventory, rewritten on import, and never deployed as source"),
    (".pyc", "as above, the individual cache files"),
    (".pyo", "optimised CPython bytecode, generated from the same .py sources and not deployed"),
    (".DS_Store", "macOS finder metadata; carries no application behaviour"),
    (".gitkeep", "a zero-byte placeholder that exists only so git records an empty directory"),
)


def _excluded(rel: str) -> str | None:
    """Returns the exclusion reason when a path is excluded, else None."""
    parts = rel.split("/")
    for pattern, why in EXCLUSIONS:
        if pattern.startswith("."):
            if rel.endswith(pattern) or parts[-1] == pattern:
                return why
        elif pattern in parts:
            return why
    return None


def _tracked_paths() -> set[str]:
    """Paths git tracks, used to REPORT tracked state, never to filter the walk."""
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"],
                         capture_output=True, text=True, check=True).stdout
    return {line for line in out.splitlines() if line}


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_production(root: pathlib.Path | None = None,
                    roots: tuple[tuple[str, bool, str], ...] | None = None
                    ) -> list[tuple[str, str, int, bool]]:
    """
    Discovers the production surface FROM THE FILESYSTEM.

    Returns (relative_path, sha256, size_bytes, is_tracked) sorted by path in plain byte order,
    which is the canonical ordering: it depends on nothing but the names themselves, so two
    checkouts on two machines in two locales produce the identical sequence.

    Only metadata that is explicitly non-semantic is normalised: the path separator is forced to
    "/" so a manifest is portable, and nothing else. Mode, mtime, owner and inode are NOT
    recorded, because a checkout legitimately changes all four without changing a byte the
    application reads. File CONTENT is hashed exactly as it sits, with no newline or encoding
    normalisation, so a line-ending change is a change.
    """
    # ROOT BY DEFAULT, but any directory may be walked. The non-vacuity campaign copies the
    # production tree into a temporary directory and mutates THAT, so the four mutations are
    # proved to turn the guard red without ever mutating the real repository; and the same
    # function is then run once against the real ROOT so the deployed guard is the thing proved.
    root = ROOT if root is None else root
    tracked = _tracked_paths() if root == ROOT else set()
    found: dict[str, pathlib.Path] = {}
    for rel, recursive, _why in (PRODUCTION_ROOTS if roots is None else roots):
        base = root / rel
        if not base.exists():
            raise FileNotFoundError(
                f"production root {rel!r} does not exist. A root that has vanished is a freeze "
                f"failure, not something to skip silently.")
        if recursive:
            if not base.is_dir():
                raise NotADirectoryError(f"recursive production root {rel!r} is not a directory")
            for p in base.rglob("*"):
                if not p.is_file():
                    continue
                r = p.relative_to(root).as_posix()
                if _excluded(r):
                    continue
                found[r] = p
        else:
            if not base.is_file():
                raise FileNotFoundError(f"production root {rel!r} is not a file")
            found[base.relative_to(root).as_posix()] = base
    return [(r, sha256_file(found[r]), found[r].stat().st_size, r in tracked)
            for r in sorted(found)]


def manifest_lines(root: pathlib.Path | None = None, roots=None) -> list[str]:
    """The canonical manifest text: one `sha256  path` line per file, byte-sorted by path."""
    return [f"{digest}  {rel}" for rel, digest, _size, _tracked in walk_production(root, roots)]


def manifest_text(root: pathlib.Path | None = None, roots=None) -> str:
    return "\n".join(manifest_lines(root, roots)) + "\n"


def manifest_sha256(root: pathlib.Path | None = None, roots=None) -> str:
    """The hash OF THE MANIFEST, so the list of files is itself pinned, not only its contents."""
    return hashlib.sha256(manifest_text(root, roots).encode("utf-8")).hexdigest()


#: Where the pinned expected manifest lives. It is the RECORD of what the walk found when the
#: freeze was taken. It is never the source of the file names.
#:
#: RUN 24. This moved again, from run23_production_tree.sha256 to the run24 file, because
#: assets/js/neural_flow.js changed once more (the Signal Flow empty-state gate). The run22 and
#: run23 manifests are BOTH kept exactly as they were written, as those releases' historical
#: records; the Run-24 freeze names run23 as its parent and carries its digest.
#:
#: POST-RUN-22 UI CORRECTION. This moved from run22_production_tree.sha256 to the run23 file
#: because three production UI files changed after the Run-22 freeze was taken. The Run-22
#: manifest is NOT rewritten: it stays exactly as Run 22 wrote it, as that release's historical
#: record, and the superseding freeze names it as its parent and carries its digest. Repointing
#: rather than editing is the whole distinction the freeze rests on -- a baseline regenerated in
#: place agrees with production by construction and can never catch an undeclared edit.
#: RUN 28. Repointed again, and for the first time because ANALYTICAL production code changed
#: rather than a UI file. The owner's Run-28 supervisory contract authorises modification of v3
#: analytical production code for the Category 1 to 3 scope; the guard was turned red first and
#: observed, then repointed. The run26 manifest is NOT rewritten: it stays exactly as Run 26
#: wrote it, as that release's historical record, and the superseding freeze names it as its
#: parent and carries its digest.
#: RUN 28 CLOSURE. Repointed once more, and NOT by regenerating the Run-28 file. The owner's
#: closure instruction requires Run 28's own defects closed: the two approved renames propagated
#: to every current surface, the A1.1 drift closed to the name the authority records, and a real
#: intake path built for the twenty abstaining modules. Fourteen production files moved and one
#: was created. The run28 manifest is NOT rewritten: it stays exactly as Run 28 wrote it, as that
#: release's historical record, and this successor names it as its parent and carries its digest
#: in research/freeze/RUN28_CLOSURE_FREEZE_2026-08-14.json. Repointing rather than editing is the
#: whole distinction the freeze rests on.
#: RUN 29. Repointed again, for the same reason and by the same discipline: the owner's Run-29
#: supervisory contract authorises modification of analytical production code, data contracts and
#: new governed structures for the Category 4 and 5 scope. Eight production files moved and one
#: was created. The run28 closure manifest is NOT rewritten: it stays exactly as that closure
#: wrote it, as that release's historical record, and this successor names it as its parent and
#: carries its digest in research/freeze/RUN29_CANONICAL_CAT4_5_FREEZE_2026-08-16.json. The guard
#: was turned red first and observed reporting the eight changed files and the one added one.
#: RUN 29 CLOSURE. Repointed once more, and again NOT by regenerating its parent. The closure
#: decomposed Run 29's own too-broad `real_corpus_populated = no` claim and found ONE structure
#: whose defining fields the corpus already extracted and which no production code assembled:
#: `ncrExposureRecord`. Wiring it is production corpus-to-structure assembly, so it moved the
#: analytical line to sim-2026.08-v14 and four production files changed. The run29 manifest is
#: NOT rewritten: it stays exactly as Run 29 wrote it, as that release's historical record, and
#: this successor names it as its parent and carries its digest in
#: research/freeze/RUN29_CLOSURE_FREEZE_2026-08-16.json. The guard was turned red first and
#: observed reporting the four changed files.
#: RUN 30. Repointed again, by the same discipline and for the same kind of reason: the owner's
#: Run-30 supervisory contract authorises modification of Category-6/7 analytical production
#: code, of evidence and data contracts, and the addition of the epistemic and decision
#: structures those methods are defined on. One production file moved -- models_gov.py, where the
#: three Category-6 comparison ensembles stopped voting the whole module array and started
#: synthesising the independent governed signals -- one was extended (project_data.py, the intake
#: vocabulary) and one was created (canonical_v5.py, the v5 canonical layer). The run29 closure
#: manifest is NOT rewritten: it stays exactly as that closure wrote it, as that release's
#: historical record, and this successor names it as its parent and carries its digest in
#: research/freeze/RUN30_CANONICAL_CAT6_7_FREEZE_2026-08-16.json. The guard was turned red first
#: and observed reporting the added file and the changed one.
#: RUN 30 CLOSURE. Repointed once more, and NOT by regenerating its parent. Run 30's own report
#: disclosed that the twenty Category-7 operational runners still executed v14 proxy arithmetic
#: while the canonical layer sat unreached; the closure repoints all twenty through
#: models_cat7.py, which is new production code, and removes the eight proxy qualifiers and three
#: truthful method labels that repointing made false. The run30 manifest is NOT rewritten: it
#: stays exactly as Run 30's first pass wrote it, as that release's historical record, and this
#: successor names it as its parent and carries its digest in
#: research/freeze/RUN30_CLOSURE_FREEZE_2026-08-16.json. The guard was turned red first and
#: observed reporting the added file and the four changed ones.
PINNED = ROOT / "code_audit" / "run30_closure_production_tree.sha256"
#: The Run-30 canonical manifest, the immediate parent of the current one, kept addressable so a
#: guard can prove the supersession is a real change and not a silent rewrite.
PINNED_RUN30 = ROOT / "code_audit" / "run30_production_tree.sha256"
#: The Run-29 closure manifest, the immediate parent of the current one, kept addressable so a
#: guard can prove the supersession is a real change and not a silent rewrite.
PINNED_RUN29_CLOSURE = ROOT / "code_audit" / "run29_closure_production_tree.sha256"
#: The Run-29 canonical manifest, the immediate parent of the current one, kept addressable so a
#: guard can prove the supersession is a real change and not a silent rewrite.
PINNED_RUN29 = ROOT / "code_audit" / "run29_production_tree.sha256"
#: The Run-28 closure manifest, the immediate parent of the current one, kept addressable so a
#: guard can prove the supersession is a real change and not a silent rewrite.
PINNED_RUN28 = ROOT / "code_audit" / "run28_production_tree.sha256"
#: The Run-22 manifest, kept addressable so a guard can prove the supersession is a real change
#: and not a silent rewrite.
PINNED_RUN22 = ROOT / "code_audit" / "run22_production_tree.sha256"
#: The post-Run-22 manifest, the immediate parent of the current one, kept addressable for the
#: same reason.
PINNED_RUN23 = ROOT / "code_audit" / "run23_production_tree.sha256"
#: The Run-24 manifest, kept addressable for the same reason.
PINNED_RUN24 = ROOT / "code_audit" / "run24_production_tree.sha256"
#: The Run-25 manifest, the immediate parent of the current one, kept addressable for the
#: same reason.
PINNED_RUN25 = ROOT / "code_audit" / "run25_production_tree.sha256"
#: The Run-26 manifest, the immediate parent of the current one, kept addressable for the
#: same reason.
PINNED_RUN26 = ROOT / "code_audit" / "run26_production_tree.sha256"
#: The same, for the scientific authority tree.
PINNED_AUTHORITY = ROOT / "code_audit" / "run22_authority_tree.sha256"


def compare(root: pathlib.Path | None = None,
            pinned_text: str | None = None,
            roots=None, pinned_path: pathlib.Path | None = None) -> dict[str, list[str]]:
    """
    The four ways production can differ from the freeze, kept apart so the guard can say WHICH.

    added    -- in the tree, not in the pinned manifest. The blind spot item 5 is about.
    removed  -- in the pinned manifest, no longer in the tree.
    changed  -- in both, different bytes.
    A rename shows up as one `added` and one `removed`; `renamed` pairs those whose CONTENT
    hash matches, so a moved file is reported as a move rather than as an unrelated pair.
    """
    now = {rel: digest for rel, digest, _s, _t in walk_production(root, roots)}
    pinned: dict[str, str] = {}
    _pin_file = PINNED if pinned_path is None else pinned_path
    text = _pin_file.read_text(encoding="utf-8") if pinned_text is None else pinned_text
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        digest, _, rel = line.partition("  ")
        pinned[rel] = digest
    added = sorted(set(now) - set(pinned))
    removed = sorted(set(pinned) - set(now))
    changed = sorted(r for r in set(now) & set(pinned) if now[r] != pinned[r])
    renamed = sorted(f"{old} -> {new}" for old in removed for new in added
                     if pinned[old] == now[new])
    return {"added": added, "removed": removed, "changed": changed, "renamed": renamed}


if __name__ == "__main__":
    import sys

    _groups = (("production", None, PINNED), ("authority", AUTHORITY_ROOTS, PINNED_AUTHORITY))
    if "--write" in sys.argv:
        for label, roots, pin in _groups:
            pin.write_text(manifest_text(None, roots), encoding="utf-8")
            print(f"wrote {pin.relative_to(ROOT)}: {len(manifest_lines(None, roots))} files "
                  f"({label})")
            print(f"  manifest sha256: {manifest_sha256(None, roots)}")
    else:
        bad = False
        for label, roots, pin in _groups:
            d = compare(None, None, roots, pin)
            for k in ("added", "removed", "changed", "renamed"):
                for v in d[k]:
                    print(f"{label} {k.upper():8} {v}")
            bad = bad or any(d[k] for k in ("added", "removed", "changed"))
            print(f"{label}: {len(manifest_lines(None, roots))} files  "
                  f"manifest sha256: {manifest_sha256(None, roots)}")
        sys.exit(1 if bad else 0)
