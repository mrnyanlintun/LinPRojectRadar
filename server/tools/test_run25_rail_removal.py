#!/usr/bin/env python3
"""
RUN 25. "REMOVE THE LEFT RAIL, AND MAKE AN EMPTY PROJECT LOOK EMPTY." SOURCE GUARDS.

OWNER-DIRECTED CONTRACT CHANGE, 2026-08-14. Earlier owner instructions said the numbered
Signal rail stays; Runs 16, 23 and 24 guarded its presence. The owner's 2026-08-14
instruction orders the LEFT RAIL REMOVED ENTIRELY, and this suite is the standing guard of
the NEW contract: no rail marker in any served source, the empty-project gate merged at
26597e8 undisturbed, the freeze chain extended by supersession rather than rewrite, and the
reversal recorded in the anti-fossilization register.

Every check is against shipped markers, never a copy of the logic, and every absence
predicate is proved capable of failing by a mutation whose application is confirmed before
its red is believed. Browser-level evidence (rail absent at five viewport widths, empty and
computed side by side) is server/tools/drive_run25_rail_removal.py.

Run:
    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_run25_rail_removal.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]

INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
DETAIL = (ROOT / "assets" / "js" / "detail.js").read_text(encoding="utf-8")
CSS = (ROOT / "assets" / "css" / "radar.css").read_text(encoding="utf-8")
FLOW = (ROOT / "assets" / "js" / "neural_flow.js").read_text(encoding="utf-8")
APP = (ROOT / "assets" / "js" / "app.js").read_text(encoding="utf-8")

passed = total = 0
failures: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global passed, total
    total += 1
    if ok:
        passed += 1
        print(f"  PASS  {label}")
    else:
        failures.append(label + ("  [" + detail[:220] + "]" if detail else ""))
        print(f"  ****  {label}" + (f"  [{detail[:220]}]" if detail else ""))


print("=" * 78)
print("SECTION 1  the rail is gone from every served source")
print("=" * 78)

RAIL_MARKERS = ("detail-secnav", "buildSectionNav", "data-secnav-target", "secNavObserver")
for name, text in (("index.html", INDEX), ("detail.js", DETAIL), ("radar.css", CSS),
                   ("neural_flow.js", FLOW)):
    for m in RAIL_MARKERS:
        check(m not in text, f"{name} carries no rail marker {m!r}")

# The rail's targets survive it: the collapsible-section machinery is untouched.
check("window.toggleSection = function" in APP and "collapse-section" in APP,
      "the collapsible sections the rail used to list still exist and still toggle (app.js)")
check("lin:section-opened" in DETAIL,
      "and the lazy section-initialisation event wiring in detail.js is untouched")

print()
print("=" * 78)
print("SECTION 2  the empty-project gate merged at 26597e8 is undisturbed")
print("=" * 78)

for m, why in (("lnf-empty", "the empty-state panel"),
               ("lnf-reveal", "the explicit reveal control"),
               ("aria-expanded", "its published expanded state"),
               ("drawDiagram", "the renamed draw function whose emptiness decision gates it")):
    check(m in FLOW, f"neural_flow.js still ships {why} ({m!r})")
check("no uploaded documents and no current results" in FLOW,
      "and the empty-project sentence is still the shipped one")

print()
print("=" * 78)
print("SECTION 3  the superseding freeze chain")
print("=" * 78)

_stage1 = ROOT / "research" / "freeze" / "RUN25_RAIL_REMOVAL_FREEZE_2026-08-14.json"
check(_stage1.is_file(), "the Run-25 stage-1 freeze manifest exists")
_doc = json.loads(_stage1.read_text(encoding="utf-8"))
check(_doc.get("release_identifier")
      == "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN25-RAIL-REMOVAL-1",
      "it names the Run-25 release identifier")
check(_doc.get("supersedes")
      == "OPUS-GUBERNATIO-RESEARCH-INSTRUMENT-2026-08-14-RUN24-EMPTY-DIAGRAM-1",
      "and supersedes the Run-24 release by name")
_parent = ROOT / "research" / "freeze" / "RUN24_EMPTY_PROJECT_DIAGRAM_FREEZE_2026-08-14.json"
check(_doc.get("supersedes_manifest_sha256")
      == hashlib.sha256(_parent.read_bytes()).hexdigest(),
      "the recorded parent digest matches the parent manifest's actual bytes")
_git24 = subprocess.run(["git", "-C", str(ROOT), "show",
                         "017c95e:research/freeze/RUN24_EMPTY_PROJECT_DIAGRAM_FREEZE_2026-08-14.json"],
                        capture_output=True, text=True)
check(_git24.returncode == 0
      and _git24.stdout == _parent.read_text(encoding="utf-8"),
      "the Run-24 manifest is preserved byte-for-byte as it stood at the starting commit: the "
      "supersession does not rewrite historical evidence")

_run24 = ROOT / "code_audit" / "run24_production_tree.sha256"
_run25 = ROOT / "code_audit" / "run25_production_tree.sha256"
check(_run24.is_file() and _run25.is_file(),
      "both the Run-24 production-tree manifest and the superseding Run-25 one exist")


def _rows(path: pathlib.Path) -> dict[str, str]:
    return {ln.partition("  ")[2]: ln.partition("  ")[0]
            for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()}


_a, _b = _rows(_run24), _rows(_run25)
check(set(_a) == set(_b),
      "the superseding tree manifest names exactly the same production files: the rail "
      "removal added and removed no file", str(sorted(set(_a) ^ set(_b))))
_moved = sorted(k for k in _a if _a[k] != _b[k])
check(_moved == ["assets/css/radar.css", "assets/js/detail.js", "index.html"],
      "and the ONLY files whose bytes moved are the three the rail lived in", str(_moved))

sys.path.insert(0, str(ROOT / "server" / "tools"))
import production_tree as pt  # noqa: E402

# RUN 26 REPOINTED THE PIN, AND THIS CHECK IS ABOUT SUPERSESSION, NOT ABOUT RUN 25 BEING LAST.
# The property Run 25 needed is that its manifest exists, is addressable, and is the parent of
# whatever the current pin is; pinning the CURRENT pin to Run 25's name would have made every
# later freeze impossible, which is fossilization rather than protection. The Run-25 manifest is
# still required to exist unchanged, and it is still required to be the pin's immediate parent.
check(pt.PINNED_RUN25.name == "run25_production_tree.sha256"
      and pt.PINNED_RUN25.is_file(),
      "the Run-25 manifest is still present and addressable after being superseded")
# RUN 28 repointed the pin again, for the first time because ANALYTICAL production code changed
# rather than a UI file. The chain of accepted pins is EXTENDED, not opened: the guard still
# requires the pin to be one of the named manifests in the chain, so a pin at an unnamed or
# invented file is still red.
# THE RUN-28 CLOSURE extends the chain once more, for the same reason and by the same rule: the
# owner's closure instruction moved fourteen production files and created one, so the pin moves
# to the closure manifest and the Run-28 manifest is kept addressable as its parent rather than
# rewritten. The chain is EXTENDED, not opened; a pin at an unnamed file is still red.
# RUN 29 extends the chain once more, for the same reason and by the same rule: the owner's
# Run-29 contract moved eight production files and created one, so the pin moves to the Run-29
# manifest and the closure manifest is kept addressable as its parent rather than rewritten.
# THE RUN-29 CLOSURE extends it once more. The closure wired one canonical structure --
# `ncrExposureRecord` -- out of corpus fields the extraction pipeline already produced, which is
# production corpus-to-structure assembly and moved the analytical line to sim-2026.08-v14. Four
# production files changed, so the pin moves to the closure manifest and the Run-29 manifest is
# kept addressable as its parent rather than rewritten.
check(pt.PINNED.name in ("run25_production_tree.sha256", "run26_production_tree.sha256",
                        "run28_production_tree.sha256",
                        "run28_closure_production_tree.sha256",
                        "run29_production_tree.sha256",
                        "run29_closure_production_tree.sha256",
                        # RUN 30 supersedes it once more: the Category-6/7 canonical remediation
                        # added canonical_v5.py, moved models_gov.py and extended
                        # project_data.py. The Run-29 closure manifest is kept addressable as
                        # this one's parent rather than rewritten.
                        "run30_production_tree.sha256"),
      "the freeze guard's pinned manifest is the Run-25 one or one of the manifests that "
      "supersede it "
      "it", pt.PINNED.name)
if pt.PINNED.name != "run25_production_tree.sha256":
    _p25 = {ln.split("  ", 1)[1]: ln.split("  ", 1)[0]
            for ln in pt.PINNED_RUN25.read_text(encoding="utf-8").splitlines() if ln.strip()}
    _p26 = {ln.split("  ", 1)[1]: ln.split("  ", 1)[0]
            for ln in pt.PINNED_RUN26.read_text(encoding="utf-8").splitlines() if ln.strip()}
    _now = {ln.split("  ", 1)[1]: ln.split("  ", 1)[0]
            for ln in pt.PINNED.read_text(encoding="utf-8").splitlines() if ln.strip()}
    # RUN 25 -> RUN 26 is unchanged and is still asserted exactly, against the Run-26 manifest
    # itself rather than against whatever the pin currently points at, so a later run cannot
    # dilute Run 26's own record by moving the pin.
    check(set(_p25) == set(_p26),
          "the superseding manifest covers exactly the same file list, so the freeze was not "
          "narrowed while it was moved",
          str(sorted(set(_p25) ^ set(_p26))))
    check(sorted(k for k in _p25 if _p25[k] != _p26[k])
          == ["assets/js/knowledge.js", "assets/js/neural_flow.js", "index.html"],
          "and only the three files Run 26 declares moved between the two manifests",
          str(sorted(k for k in _p25 if _p25[k] != _p26[k])))
    # RUN 26 -> RUN 28. The freeze was WIDENED and not narrowed: the file list gains the v3
    # canonical method layer and loses nothing, and the files whose bytes moved are exactly the
    # ones Run 28's own manifest declares plus the three Run 20 already declares and Run 28
    # deliberately does not declare twice.
    if pt.PINNED.name == "run28_production_tree.sha256":
        from run28_production_changes import (  # noqa: E402
            RUN28_NEW_PRODUCTION_FILES, RUN28_PRODUCTION_CHANGES,
        )
        check(set(_p26) <= set(_now),
              "the Run-28 manifest covers everything the Run-26 one did, so the freeze was "
              "widened rather than narrowed", str(sorted(set(_p26) - set(_now))))
        check(sorted(set(_now) - set(_p26)) == sorted(RUN28_NEW_PRODUCTION_FILES),
              "and the only file it adds is the one Run 28 declares as new production code",
              str(sorted(set(_now) - set(_p26))))
        _moved = sorted(k for k in _p26 if k in _now and _p26[k] != _now[k])
        _declared_28 = {e[1] for e in RUN28_PRODUCTION_CHANGES.values()}
        # The five paths Run 20 already declares against the immovable Run-20 freeze. Run 28
        # changed all five again and deliberately does NOT declare any of them a second time,
        # because the declared-changes guard requires that no path appear in two manifests.
        _already = {"server/app/simulation/models_ext.py",
                    "server/app/simulation/registry.py",
                    "server/app/simulation/method_labels.py",
                    "server/app/simulation/lineage.py",
                    "server/app/simulation/parameters.py"}
        check(set(_moved) <= (_declared_28 | _already),
              "and every file whose bytes moved between the two is declared by Run 28 or was "
              "already declared against the Run-20 freeze by an earlier run",
              str(sorted(set(_moved) - (_declared_28 | _already))))
    # RUN 26 -> RUN 28 CLOSURE. The pin is now two links further on, so the Run-26 comparison
    # above is made against the RUN-28 manifest itself rather than against the moving pin, and
    # the closure link is asserted on its own terms: widened not narrowed, one new file, and
    # every file whose bytes moved declared by the Run-28 manifest or already declared against
    # the Run-20 freeze by an earlier run.
    if pt.PINNED.name == "run28_closure_production_tree.sha256":
        from run28_production_changes import (  # noqa: E402,F811
            RUN28_NEW_PRODUCTION_FILES, RUN28_PRODUCTION_CHANGES,
        )
        _p28 = {ln.split("  ", 1)[1]: ln.split("  ", 1)[0]
                for ln in pt.PINNED_RUN28.read_text(encoding="utf-8").splitlines() if ln.strip()}
        check(pt.PINNED_RUN28.is_file() and set(_p26) <= set(_p28),
              "the Run-28 manifest is still present and addressable after being superseded, and "
              "still covers everything the Run-26 one did",
              str(sorted(set(_p26) - set(_p28))))
        check(set(_p28) <= set(_now),
              "the closure manifest covers everything the Run-28 one did, so the freeze was "
              "widened rather than narrowed", str(sorted(set(_p28) - set(_now))))
        check(sorted(set(_now) - set(_p28)) == ["server/app/project_data.py"],
              "and the only file it adds is the governed project data intake, which is the "
              "supply path the twenty abstaining modules rest on",
              str(sorted(set(_now) - set(_p28))))
        _moved28 = sorted(k for k in _p28 if k in _now and _p28[k] != _now[k])
        _declared_28 = {e[1] for e in RUN28_PRODUCTION_CHANGES.values()}
        _already = {"server/app/simulation/models_ext.py",
                    "server/app/simulation/registry.py",
                    "server/app/simulation/method_labels.py",
                    "server/app/simulation/lineage.py",
                    "server/app/simulation/parameters.py",
                    "assets/js/knowledge.js", "assets/js/neural_flow.js"}
        check(set(_moved28) <= (_declared_28 | _already),
              "and every file whose bytes moved across the closure is declared by the Run-28 "
              "manifest or was already declared by an earlier run",
              str(sorted(set(_moved28) - (_declared_28 | _already))))

    # RUN 29 -> RUN 29 CLOSURE. Asserted on its own terms, with the Run-29 manifest addressed
    # directly rather than through the moving pin, so a later run cannot dilute Run 29's record.
    # The closure ADDED no production file and REMOVED none: it changed four that were already
    # declared -- models_doc.py and registry.py by Run 20, models.py and documents.py by Run 28,
    # and canonical_v4.py by Run 29 as new production code -- which is why there is no fresh
    # declared-changes manifest for it, and why the assertion below is that the file LIST is
    # identical and only declared files moved bytes.
    if pt.PINNED.name == "run29_closure_production_tree.sha256":
        _p29 = {ln.split("  ", 1)[1]: ln.split("  ", 1)[0]
                for ln in pt.PINNED_RUN29.read_text(encoding="utf-8").splitlines() if ln.strip()}
        check(pt.PINNED_RUN29.is_file() and set(_p26) <= set(_p29),
              "the Run-29 manifest is still present and addressable after being superseded, and "
              "still covers everything the Run-26 one did",
              str(sorted(set(_p26) - set(_p29))))
        check(set(_p29) == set(_now),
              "the closure manifest covers exactly the same production surface, so the freeze "
              "was neither narrowed nor widened: the closure created no production file",
              str(sorted(set(_p29) ^ set(_now))))
        _moved29 = sorted(k for k in _p29 if _p29[k] != _now[k])
        check(_moved29 == ["server/app/documents.py",
                           "server/app/simulation/canonical_v4.py",
                           "server/app/simulation/models.py",
                           "server/app/simulation/models_doc.py"],
              "and exactly the four files the closure changed moved bytes: the corpus-to-"
              "structure assembler, the canonical layer that gained the count form, the runner "
              "that reads it, and the version stamp", str(_moved29))

check(pt.PINNED_RUN24.name == "run24_production_tree.sha256",
      "and the Run-24 manifest is kept addressable, so the supersession is provable")

print()
print("=" * 78)
print("SECTION 4  the reversal is on the record as a contract change")
print("=" * 78)

_reg = (ROOT / "code_audit" / "run20_anti_fossilization_register.csv").read_text(
    encoding="utf-8")
check("OWNER_DIRECTED_CONTRACT_CHANGE" in _reg,
      "the register carries the owner-directed contract-change class")
for inst in ("test_run16_final_flow_and_rail.py::section B",
             "test_run23_signal_flow_truthfulness.py::sections 2-3",
             "test_run24_empty_project_diagram.py::navigator-untouched",
             "test_run2_fifteen_defects.py::detail.js freeze diff"):
    check(inst in _reg, f"the register names the inverted guard {inst}")

print()
print("=" * 78)
print("SECTION 5  non-vacuity: every absence predicate proved capable of failing")
print("=" * 78)

# NV-1: reinsert the rail element into a copy of index.html; the exact predicate of section 1
# must go red on that copy. The injection is confirmed to have applied first.
_mut_index = INDEX.replace('<div id="detail-root">',
                           '<nav id="detail-secnav" class="detail-secnav"></nav>'
                           '<div id="detail-root">', 1)
check(_mut_index != INDEX and 'id="detail-secnav"' in _mut_index,
      "NV-1 INJECTION TOOK EFFECT: the mutated index.html carries the rail element")
check(not all(m not in _mut_index for m in RAIL_MARKERS),
      "NV-1: the section-1 predicate goes RED on the mutated copy")
check(all(m not in INDEX for m in RAIL_MARKERS),
      "NV-1 RESTORE: the shipped index.html is still clean (baseline rechecked)")

# NV-2: reinsert the builder into a copy of detail.js.
_mut_detail = DETAIL + "\nfunction buildSectionNav(root) {}\n"
check("buildSectionNav" in _mut_detail and _mut_detail != DETAIL,
      "NV-2 INJECTION TOOK EFFECT: the mutated detail.js carries the builder")
check(not all(m not in _mut_detail for m in RAIL_MARKERS),
      "NV-2: the predicate goes RED on the mutated copy")
check(all(m not in DETAIL for m in RAIL_MARKERS),
      "NV-2 RESTORE: the shipped detail.js is still clean")

# NV-3: reinsert one rail style into a copy of radar.css.
_mut_css = CSS + "\n.detail-secnav { position: fixed; left: 12px; }\n"
check("detail-secnav" in _mut_css and _mut_css != CSS,
      "NV-3 INJECTION TOOK EFFECT: the mutated stylesheet carries a rail rule")
check(not all(m not in _mut_css for m in RAIL_MARKERS),
      "NV-3: the predicate goes RED on the mutated copy")
check(all(m not in CSS for m in RAIL_MARKERS),
      "NV-3 RESTORE: the shipped stylesheet is still clean")

# NV-4: delete the empty-gate control from a copy of neural_flow.js; section 2's predicate
# must go red.
_mut_flow = FLOW.replace("lnf-reveal", "lnf-removed")
check("lnf-reveal" not in _mut_flow and _mut_flow != FLOW,
      "NV-4 INJECTION TOOK EFFECT: the reveal control is gone from the mutated copy")
check(not ("lnf-reveal" in _mut_flow),
      "NV-4: section 2's predicate goes RED on the mutated copy")
check("lnf-reveal" in FLOW,
      "NV-4 RESTORE: the shipped neural_flow.js still carries the control")

# NV-5: corrupt a copy of the Run-25 tree manifest; the moved-files check must go red.
_mut_rows = dict(_b)
_mut_rows["assets/js/neural_flow.js"] = "0" * 64
_moved_mut = sorted(k for k in _a if _a[k] != _mut_rows[k])
check(_mut_rows != _b and _mut_rows["assets/js/neural_flow.js"] == "0" * 64,
      "NV-5 INJECTION TOOK EFFECT: a fourth file's digest is corrupted in the mutated rows")
check(_moved_mut != ["assets/css/radar.css", "assets/js/detail.js", "index.html"],
      "NV-5: the moved-files check goes RED on the mutated rows", str(_moved_mut))
check(sorted(k for k in _a if _a[k] != _b[k])
      == ["assets/css/radar.css", "assets/js/detail.js", "index.html"],
      "NV-5 RESTORE: the real manifests still move exactly the three rail files")

for f in failures:
    print("FAILED:", f)
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
