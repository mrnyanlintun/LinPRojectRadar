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
    # RUN 54. `research/deepdive.html` WAS A PRODUCTION ROOT AND IS NOT ONE ANY MORE, because
    # the file and the route that served it were both DELETED on the owner's ruling at section 8
    # of the Run 54 order. It is removed rather than left to trip walk_production()'s
    # "a root that has vanished is a freeze failure" -- that guard is correct and is deliberately
    # not softened; what changed is that this path is no longer claimed as production. The guard
    # keeps its full force over index.html and logo.png, the two non-recursive roots that remain.
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
#: RUN 30 FINAL CLOSURE. Repointed once more. The closure named a lineage state on every
#: Category-7 ledger row, which touched lineage.py and models_cat7.py. The run30 closure manifest
#: is NOT rewritten: it stays as that release wrote it, and this successor names it as its parent
#: and carries its digest in research/freeze/RUN30_FINAL_CLOSURE_FREEZE_2026-08-16.json.
#: RUN 31, PASS 1. Repointed once more, by the same discipline and for the same kind of reason:
#: the owner's Run-31 supervisory contract authorises modification of Category-8/9 analytical
#: production code, of evidence and data contracts, and the addition of the governed regulatory,
#: agent-based-governance and evidence-qualification structures those methods are defined on.
#: FIVE production files were created -- regulatory.py (the governed versioned rule layer),
#: abm.py (the agent-based governance model), qualified_evidence.py (the Category-9 qualified
#: evidence object and gate), canonical_v6.py (the v6 canonical layer) and models_cat89.py (the
#: sixteen thin operational runners) -- and TWO were changed: models.py, where the sixteen
#: Category-8/9 identities are repointed onto the canonical layer and the stamp advances to
#: sim-2026.08-v17, and project_data.py, whose governed intake vocabulary is extended with the v6
#: structure map. The run30 final closure manifest is NOT rewritten: it stays exactly as that
#: release wrote it, as that release's historical record, and this successor names it as its
#: parent and carries its digest below. The guard was turned red first and observed reporting
#: exactly those five added and two changed files.
#: RUN 32. Repointed once more, by the same discipline and for the same kind of reason: the
#: owner's Run-32 supervisory contract authorises modification of Category-10 analytical
#: production code and of the governed decision-structure intake. TWO production files were
#: created -- canonical_v7.py (the canonical Category-10 decision layer) and models_cat10.py (the
#: seven thin operational runners) -- and TWO were changed: models.py, where the seven
#: Category-10 identities are repointed onto the canonical layer and the stamp advances to
#: sim-2026.08-v20, and project_data.py, whose governed intake vocabulary is extended with the v7
#: structure map. The run31 pass-1 manifest is NOT rewritten: it stays exactly as that release
#: wrote it, as that release's historical record, and this successor names it as its parent and
#: keeps it addressable below. The guard was turned red FIRST and observed reporting exactly
#: those two added and two changed files and nothing else.
#: RUN 33. Repointed once more, by the same discipline and for the same kind of reason: the
#: owner's Run-33 supervisory contract authorises modification of Portfolio Health production
#: code and of the governed portfolio/cohort data contracts. TWO production files were created --
#: canonical_v8.py (the canonical Portfolio Health layer) and portfolio_health.py (the production
#: dispatcher) -- and FOUR were changed: documents.py, where the one production portfolio call
#: site is repointed onto the canonical route; models.py, where the stamp advances to
#: sim-2026.08-v21; project_data.py, whose governed intake vocabulary is extended with the v8
#: structure map; and registry.py, where the D1.2 proxy qualifier is withdrawn because the proxy
#: it described is gone. On the client side workspace.js loses the Portfolio Health status dots,
#: knowledge.js loses the withdrawn qualifier and the generated defensibility evidence follows.
#: The run32 manifest is NOT rewritten: it stays exactly as that release wrote it, as that
#: release's historical record, and this successor names it as its parent and keeps it
#: addressable below. The guard was turned red FIRST and observed reporting exactly those added
#: and changed files and nothing else.
#: RUN 34. Repointed once more, by the same discipline: the owner's Run-34 calibration contract
#: authorises modification of Portfolio Health parameter handling, abstention behaviour and
#: threshold application. THREE production files changed and none was created: canonical_v8.py
#: (the parameter registry, the cohort-size policy, the TWO_SIDED orientation, the withheld PH.2
#: composite, PH.3's STABLE/NOT_ESTIMABLE vocabulary and the governed calibration record),
#: portfolio_health.py (the calibration-record intake) and models.py (the stamp advances to
#: sim-2026.08-v22). The run33 manifest is NOT rewritten: it stays exactly as that release wrote
#: it and this successor names it as its parent. The guard was turned red FIRST and observed
#: reporting exactly those three changed files and nothing else.
#: RUN 35 FINAL CLOSURE SUPERSEDES IT. Three production files moved and only three:
#: models_evm.py (A1.7 and A1.8 now compute their canonical value at the application's own
#: precision, A1.7 bands from it, and the rounded numbers become explicit display fields),
#: models.py (the stamp advances to sim-2026.08-v23 with the boundary recorded) and
#: method_labels.py (the stale B1.2 and B4.4 proxy labels are withdrawn). The run34 manifest is
#: NOT rewritten: it stays exactly as that release wrote it and this successor names it as its
#: parent. The guard was turned red FIRST and observed reporting exactly those three changed
#: files and nothing else.
#: RUN 36 SUCCESSOR. Run 36's A1.1 closure changed exactly ONE production file --
#: models_sim.py, where A1.1 withdrew a status band drawn over an UNSUPPORTED parameter. The
#: run35 closure manifest is NOT rewritten: it stays exactly as that release wrote it and this
#: successor names it as its parent. The guard was observed reporting exactly that one changed
#: file and nothing else before this manifest was written.
#: RUN 41 SUCCESSOR. Run 40 confirmed two HIGH defects and the owner ruled that both be fixed
#: before participant use rather than accepted for the study period, which is what made this a
#: freeze successor rather than a repair inside v25. Three production files move and only three:
#: `server/app/main.py` (finding S1 - the document-serving boundary stops echoing the
#: client-supplied MIME and stops serving untrusted bytes inline), the ADDED migration
#: `server/alembic/versions/0026_final_lock_guard.py` (finding S2 - substantive final responses
#: become database-immutable after the final lock) and `server/app/simulation/models.py` (the
#: stamp advances to sim-2026.08-v26 with the boundary recorded). The run36 manifest is NOT
#: rewritten: it stays exactly as that release wrote it and this successor names it as its
#: parent. The guard was observed reporting exactly those files, and nothing else, before this
#: manifest was written.
#: RUN 42. This moved again, from run41_production_tree.sha256 to the run42 file, on the same
#: Run-34/35 precedent. Run 42 traced the background data-processing mechanism end to end and
#: repaired two identity losses in it, and FIVE production files move and only five:
#: `server/app/extraction_merge.py` (the per-field source record now carries the document
#: identity every observation already held), `server/app/simulation/qualification.py` (the
#: provenance and timeliness reason sentences must describe the state actually reached now that
#: those dimensions can leave PARTIAL), `server/app/simulation/compute.py` and
#: `server/app/documents.py` (the project's identity reaches the qualification record on the
#: compute path and the read path), and `server/app/simulation/models.py` (the stamp advances to
#: sim-2026.08-v27 with the boundary recorded). Nothing is added and nothing is removed. The
#: run41 manifest is NOT rewritten: it stays exactly as that release wrote it and this successor
#: names it as its parent. The guard was observed reporting exactly those five files, and
#: nothing else, before this manifest was written.
#: RUN 43. This moved again, from run42_production_tree.sha256 to the run43 file, on the same
#: Run-34/35/41/42 precedent. Run 43 retires 38 of the 101 registered modules FROM SERVICE, and
#: ELEVEN production files move: the two client taxonomy artifacts `assets/js/taxonomy.js` and
#: `assets/js/categories.js` (regenerated by build_client_taxonomy.py from the roster in
#: service), `assets/js/detail.js` and `assets/js/knowledge.js` and `index.html` (the counts a
#: participant reads, which now state three populations -- 101 registered, 63 in service, 62
#: computed), `p0-baseline/module_renumbering_map.csv` (the single authority for which modules
#: are in service), `server/app/simulation/registry.py` (the derived roster and the populations
#: built from it), `server/app/simulation/portfolio_health.py` (the offload),
#: `server/app/research_export.py` and `server/app/training.py` (the populations they enumerate)
#: and `server/app/simulation/models.py` (the stamp advances to sim-2026.08-v28 with the
#: boundary recorded). Nothing is added and nothing is removed. The run42 manifest is NOT
#: rewritten: it stays exactly as that release wrote it and this successor names it as its
#: parent. The guard was observed reporting exactly those eleven files, and nothing else, before
#: this manifest was written.
#: RUN 44. This moved again, from run43_production_tree.sha256 to the run44 file, on the same
#: Run-34/35/41/42/43 precedent. Run 44 repairs the four participant-facing render defects Run 43J
#: diagnosed, and SIX production files move: `assets/js/detail.js` (one shared case-insensitive
#: severity rank in place of two capitalised-only order maps, a guard so no site names a module as
#: the driver of a severity better than its own, and an absent document-risk score rendering as
#: absent while a genuine stored zero still renders), `assets/js/signals.js` (CPI and SPI labelled
#: computed rather than extracted), `assets/js/deepdive.js` (the Portfolio Health flyout's reason
#: sentence, the ONE sequence-bearing file the owner authorised this run to move, at section 4.4),
#: `assets/css/radar.css` (one added rule for the computed mark),
#: `server/app/simulation/registry.py` (a DOCSTRING only -- `available_modules()` described the
#: retirement-reason refusal Phase F withdrew; its body is untouched and every one of the 101
#: emitted rows is byte-identical to v28) and `server/app/simulation/models.py` (the stamp
#: advances to sim-2026.08-v29 with the boundary recorded). Nothing is added and nothing is
#: removed. The run43 manifest is NOT rewritten: it stays exactly as that release wrote it and
#: this successor names it as its parent. The guard was observed reporting exactly those six
#: files, and nothing else, before this manifest was written.
#: RUN 45. This moved again, from run44_production_tree.sha256 to the run45 file, on the same
#: RUN 47 supersedes the Run-45 manifest. THREE production files move and ONE is added:
#: `server/app/evm_consistency.py` (new: the pure comparison of a document's stated value with
#: the value its own percentage implies against a known budget at completion),
#: `server/app/documents.py` (the served result carries `consistency_findings`, derived at read
#: time from the stored row by that pure function, exactly as `recommendation_basis` is),
#: `assets/js/detail.js` (the executive brief renders the disagreement as text, and
#: `BRIEF_CAT_LABEL`'s ten retired "Cat N" labels become groups and purposes) and
#: `assets/js/recommendation_options.js` (the same text beside the recommendation).
#: `server/app/simulation/models.py` carries the stamp to sim-2026.08-v31 with the boundary
#: recorded. NOTHING IS REMOVED, no stored figure moves, and no user-facing control was added,
#: moved or removed. The run45 manifest is NOT rewritten.
#: Run-34/35/41/42/43/44 precedent. Run 45 closes the period-scoping fall-through Run 44
#: measured, and FOUR production files move: `server/app/field_registry.py` (the canonical
#: IDENTITY/PERIOD/UNDETERMINED classification the owner signed off, and `retrieval_kind()`),
#: `server/app/extraction_merge.py` (`select_signal_inputs` takes the earlier periods'
#: identity observations and resolves them by the SAME per-field rule, which is what makes
#: declared document-type precedence hold across periods; `docDate` still derives from the
#: period's own observations alone), `server/app/documents.py`
#: (`_identity_observations_before`, and the two selection sites that pass it) and
#: `server/app/simulation/models.py` (the stamp advances to sim-2026.08-v30 with the boundary
#: recorded). Nothing is added and nothing is removed, and no participant-facing control moved.
#: The run44 manifest is NOT rewritten: it stays exactly as that release wrote it and this
#: successor names it as its parent. The guard was observed reporting exactly those four files,
#: and nothing else, before this manifest was written.
#: RUN 48 supersedes the Run-47 manifest. FIVE production files move and NOTHING is added or
#: removed: `server/app/documents.py` (`_computed_periods` and `_latest_computed_period`, read
#: from the result table, and the two derived read-only fields `projectperiods` now returns),
#: `assets/js/detail.js` (the detail page reads back the stored row for the latest COMPUTED
#: period instead of for the literal 1, sends no category identifier into the brief's model
#: prompt, and loses the dead category label map), `assets/js/deepdive.js` (the panel labels
#: become groups and purposes and the grouping number is declared separately from them),
#: `assets/js/charts3d.js` (one chart node label) and `server/app/simulation/models.py` (the
#: stamp advances to sim-2026.08-v32 with the boundary recorded). The guard was observed
#: reporting exactly those five files, and nothing else, before this manifest was written. The
#: run47 manifest is NOT rewritten: it stays exactly as that release wrote it and this successor
#: names it as its parent.
#: RUN 49 SUPERSEDES IT. The completion of the naming correction moved FOUR production files:
#: `assets/js/deepdive.js` (every surviving rendered instance of the retired "Cat N" scheme, and
#: the panel label map extended to all seventy-seven keys the call sites pass),
#: `assets/js/detail.js` (one section title's ampersand and the executive brief's prompt),
#: `assets/js/decision-ui.js` (COMMENTS ONLY at the three inert period literals) and
#: `server/app/simulation/models.py` (the stamp advances to sim-2026.08-v33 with the boundary
#: recorded). The guard was observed reporting exactly those four files, and nothing added,
#: removed or renamed, before this manifest was written. The run48 manifest is NOT rewritten: it
#: stays exactly as that release wrote it and this successor names it as its parent.
#: RUN 51 SUPERSEDES IT. The delivery of the six rulings Run 50 stopped on moved TWENTY-SIX
#: production files: the twenty-three participant-visible files the v19 package record names one
#: by one, plus `server/app/simulation/models.py` (the stamp advances to sim-2026.08-v34 with the
#: boundary recorded), `server/tools/taxonomy_authority.json` (the taxonomy's primary key is
#: named `key` rather than `num`, so a render site cannot mistake it for a label) and
#: `server/tools/build_client_taxonomy.py` (it emits that key and, new, a derived counts block so
#: no served page has to type a population). The guard was observed reporting exactly those
#: files, and nothing added, removed or renamed, before this manifest was written. The run49
#: manifest is NOT rewritten: it stays exactly as that release wrote it and this successor names
#: it as its parent.
#: RUN 52 SUPERSEDES IT. Eight production files moved: the SEVEN participant-visible files the
#: v20 package record names one by one, plus `server/app/simulation/models.py` (the stamp
#: advances to sim-2026.08-v35 with the boundary recorded). The guard was observed reporting
#: exactly those eight files CHANGED, and nothing added, removed or renamed, before this
#: manifest was written. `assets/js/app.js` is NOT among them: ruling 1 was stopped under
#: section 8.1 of the Run 52 order after a browser established that Manage does not reach the
#: project detail page and that Open is the only route to it. The run51 manifest is NOT
#: rewritten: it stays exactly as that release wrote it and this successor names it as its
#: parent.
#: RUNS 54 AND 55 SUPERSEDE IT, and this is the first supersession in this chain in which a
#: production ROOT ENTRY DISAPPEARS rather than merely changing. NINE production files moved:
#: TWO REMOVED -- `assets/js/deepdive.js` and `research/deepdive.html`, the client-side deep-dive
#: surface, reached by no route the service serves -- and SEVEN CHANGED: `assets/js/app.js` (the
#: project list's Manage control navigates to the project detail page; the redundant Open control
#: is removed, in that order and verified in a real browser before the removal),
#: `assets/js/ingest.js` and `assets/js/detail.js` (the six operational admin controls MOVE onto
#: the detail page of the project being viewed), `assets/css/radar.css` (the four dead .li-open
#: rules go with the control they styled), `index.html` (a COMMENT that pointed at the deleted
#: file; no rendered text moved), `server/app/main.py` (the route that served the deleted page is
#: gone, because a route serving a deleted page would be a second front door) and
#: `server/app/simulation/models.py` (the stamp advances to sim-2026.08-v36 with the boundary
#: recorded). The guard was observed reporting exactly those nine -- two REMOVED, seven CHANGED,
#: nothing added and nothing renamed -- before this manifest was written. The `removed` case is
#: NOT softened anywhere: `production_tree.py`'s own rule that a root which has vanished is a
#: freeze failure still stands, and `assets/js` and `research` are both still roots. The run52
#: manifest is NOT rewritten: it stays exactly as that release wrote it and this successor names
#: it as its parent.
#: RUN 56 SUPERSEDES IT, and this supersession is a SMALL one that says so rather than dressing
#: itself up. EXACTLY TWO production files moved and NOTHING was added, removed or renamed:
#: `assets/js/ingest.js` -- the duplicate "Upload documents" control (.pe-populate) is removed
#: FROM THE DETAIL PAGE ONLY, because the page already carried .detail-upload calling the same
#: function with the same project id, and Archive and Reset signals gain a confirmation built on
#: the LinUI.openModal shape the application already uses for its destructive project-scoped
#: actions -- and `server/app/simulation/models.py` (the stamp advances to sim-2026.08-v37 with
#: the boundary recorded). The ordered removal of `.detail-reset` was STOPPED under section 9.1
#: of the Run 56 order because NEITHER reset control is a superset of the other, so
#: `assets/js/detail.js` did NOT move and is deliberately absent from this list. The guard was
#: observed reporting exactly those two CHANGED, nothing added, removed or renamed, before this
#: manifest was written. The run55 manifest is NOT rewritten: it stays exactly as that release
#: wrote it and this successor names it as its parent.
PINNED = ROOT / "code_audit" / "run56_production_tree.sha256"
#: The Run-55 manifest, the immediate parent, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN55 = ROOT / "code_audit" / "run55_production_tree.sha256"
#: The Run-52 manifest, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN52 = ROOT / "code_audit" / "run52_production_tree.sha256"
#: The Run-51 manifest, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN51 = ROOT / "code_audit" / "run51_production_tree.sha256"
#: The Run-49 manifest, the immediate parent, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN49 = ROOT / "code_audit" / "run49_production_tree.sha256"
#: The Run-48 manifest, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN48 = ROOT / "code_audit" / "run48_production_tree.sha256"
#: The Run-47 manifest, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN47 = ROOT / "code_audit" / "run47_production_tree.sha256"
#: The Run-45 manifest, the immediate parent, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite. (Run 46 was report-only and wrote no
#: manifest, so Run 45 is the parent.)
PINNED_RUN45 = ROOT / "code_audit" / "run45_production_tree.sha256"
#: The Run-44 manifest, the immediate parent, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN44 = ROOT / "code_audit" / "run44_production_tree.sha256"
#: The Run-43 manifest, kept addressable for the same reason.
PINNED_RUN43 = ROOT / "code_audit" / "run43_production_tree.sha256"
#: The Run-42 manifest, kept addressable so a guard can prove the supersession is a real
#: change and not a silent rewrite.
PINNED_RUN42 = ROOT / "code_audit" / "run42_production_tree.sha256"
#: The Run-41 manifest, the immediate parent, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN41 = ROOT / "code_audit" / "run41_production_tree.sha256"
#: The Run-36 manifest, the immediate parent, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN36 = ROOT / "code_audit" / "run36_production_tree.sha256"
#: The Run-35 closure manifest, kept addressable so a guard can prove the supersession is a real
#: change and not a silent rewrite.
PINNED_RUN35_CLOSURE = ROOT / "code_audit" / "run35_closure_production_tree.sha256"
#: The Run-34 manifest, the immediate parent, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN34 = ROOT / "code_audit" / "run34_production_tree.sha256"
#: The Run-33 manifest, the immediate parent, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN33 = ROOT / "code_audit" / "run33_production_tree.sha256"
#: The Run-32 manifest, the immediate parent, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN32 = ROOT / "code_audit" / "run32_production_tree.sha256"
#: The Run-31 pass-1 manifest, the immediate parent, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN31_PASS1 = ROOT / "code_audit" / "run31_pass1_production_tree.sha256"
#: The Run-30 final closure manifest, the immediate parent, kept addressable so a guard can prove
#: the supersession is a real change and not a silent rewrite.
PINNED_RUN30_FINAL_CLOSURE = ROOT / "code_audit" / "run30_final_closure_production_tree.sha256"
#: The Run-30 closure manifest, the immediate parent, kept addressable so a guard can prove the
#: supersession is a real change and not a silent rewrite.
PINNED_RUN30_CLOSURE = ROOT / "code_audit" / "run30_closure_production_tree.sha256"
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
#: RUN 34 REPOINTS THE AUTHORITY MANIFEST TOO, for the first time since Run 22. The predeclared
#: calibration protocol is a scientific authority document -- it is what makes the Run-34
#: parameter decisions auditable -- so it belongs inside the authority tree rather than beside
#: it. The Run-22 record is kept addressable and is NOT rewritten.
#: RUN 35 REPOINTS IT AGAIN, for the same reason and by the same rule. The Run-35 empirical-
#: validation protocol is a scientific authority document: it fixes the eligibility vocabulary and
#: the independence rules that the whole Run-35 campaign is judged against, and it was committed
#: before any result was scored. It belongs inside the authority tree. The Run-34 and Run-22
#: records are kept addressable below and are NOT rewritten.
#: RUN 38 REPOINTS IT AGAIN, and the reason is stated plainly rather than assumed. Run 38 added
#: two documents under research/methodology -- the research data contract and the frozen analysis
#: dataset contract -- at the paths its controlling specification names. research/methodology IS
#: an AUTHORITY_ROOT, so the pin refused, correctly. These two documents govern what the study
#: record means and what may be derived from it, so they belong inside the authority tree rather
#: than beside it, and the manifest is repointed by the same mechanism Runs 34 and 35 used. The
#: Run-35, Run-34 and Run-22 records are kept addressable below and are NOT rewritten. Nothing
#: frozen moved: no file under assets/, server/app/, research_fixtures/synthetic/ or index.html
#: changed, and neither this file nor any authority manifest is named by
#: research/freeze/INSTRUMENT_FINAL_FREEZE_CHECKSUMS.csv.
#: RUN 39 REPOINTS IT AGAIN, by the same mechanism and for the same kind of reason. Run 39 added
#: research/methodology/run39_dataset_classification_contract.md at the path its controlling
#: specification names. research/methodology IS an AUTHORITY_ROOT, so the pin refused, correctly.
#: That document governs which dataset an observation belongs to -- which of TEST_ONLY, PILOT or
#: MAIN_STUDY it is, and therefore what may ever be analysed -- so it belongs inside the
#: authority tree rather than beside it. The Run-38, Run-35, Run-34 and Run-22 records are kept
#: addressable below and are NOT rewritten. Nothing frozen moved: no file under assets/,
#: server/app/, research_fixtures/synthetic/ or index.html changed, and neither this file nor any
#: authority manifest is named by research/freeze/INSTRUMENT_FINAL_FREEZE_CHECKSUMS.csv.
#: RUN 51. The AUTHORITY tree moved for the first time since Run 39: the taxonomy authority's
#: primary-key field is named `key` rather than `num`, on the owner's ruling 2 of 2026-08-22, so
#: that a render site cannot mistake the key for a label. Not one identifier, not one module and
#: not one category changed; only the name of the field that holds them. The run39 manifest is
#: NOT rewritten: it stays exactly as that release wrote it and this successor names it as its
#: parent.
#: RUN 52. The authority tree did not move: the guard reported no added, removed, changed or
#: renamed authority file, so the Run-51 authority manifest still describes it exactly and is
#: NOT superseded. A manifest is superseded when what it describes moves, not once per run.
#: RUN 55 RE-TOOK IT AND IT STILL HAS NOT MOVED. The re-take was run, not assumed: `compare()`
#: over AUTHORITY_ROOTS reported added=0 removed=0 changed=0 renamed=0, and the manifest sha256
#: recomputed from the tree, b52c47a68a20ab1629681ea240abdea2167c67f289d181f446a8170704dc1596,
#: is byte for byte the sha256 of the pinned file. So this pin is DELIBERATELY LEFT AT run51,
#: for the same reason Run 52 left it there: writing a run55 authority manifest identical to the
#: run51 one would assert a supersession that did not happen.
#: RUN 56 RE-TOOK IT AND DELIBERATELY DID NOT SUPERSEDE IT, for the third run running and for
#: the same reason: `compare()` over AUTHORITY_ROOTS reported added=0 removed=0 changed=0
#: renamed=0, and the manifest sha256 recomputed from the tree,
#: b52c47a68a20ab1629681ea240abdea2167c67f289d181f446a8170704dc1596, is byte for byte the sha256
#: of the pinned file. A manifest is superseded when what it describes moves, not once per run.
PINNED_AUTHORITY = ROOT / "code_audit" / "run51_authority_tree.sha256"
#: The Run-39 authority manifest, the immediate parent, kept addressable so a guard can prove
#: the supersession is a real change and not a silent rewrite.
PINNED_AUTHORITY_RUN39 = ROOT / "code_audit" / "run39_authority_tree.sha256"
#: The Run-38 authority manifest, kept addressable so the supersession is a real change and not a
#: silent rewrite.
PINNED_AUTHORITY_RUN38 = ROOT / "code_audit" / "run38_authority_tree.sha256"
#: The Run-35 authority manifest, kept addressable so the supersession is a real change and not a
#: silent rewrite.
PINNED_AUTHORITY_RUN35 = ROOT / "code_audit" / "run35_authority_tree.sha256"
#: The Run-34 authority manifest, kept addressable so the supersession is a real change and not a
#: silent rewrite.
PINNED_AUTHORITY_RUN34 = ROOT / "code_audit" / "run34_authority_tree.sha256"
#: The Run-22 authority manifest, kept addressable so the supersession is a real change and not a
#: silent rewrite.
PINNED_AUTHORITY_RUN22 = ROOT / "code_audit" / "run22_authority_tree.sha256"


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
