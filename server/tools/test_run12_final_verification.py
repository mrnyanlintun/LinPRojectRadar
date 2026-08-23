#!/usr/bin/env python3
"""
RUN 12, GATES 8 TO 10. The final verification: browser and server parity, defensibility and
governance, and synthetic against operational separation.

This suite does not re-derive what the Run 11 suites already assert. It asserts the things a
FINAL run has to be able to state on its own: that the participant route still has exactly one
arithmetic source, that the governed vocabulary is unchanged, that Category 9 is nowhere
described as validation, and that nothing synthetic has reached operational storage.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_run12_final_verification.py
"""

from __future__ import annotations

import pathlib
import re
import subprocess
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

ROOT = pathlib.Path(__file__).resolve().parents[2]

#: RUN 54. THE COMMIT THE DEEP-DIVE SURFACE WAS DELETED FROM, PINNED. It must NOT be written as
#: `HEAD~1`: that was true only while the deletion was the last commit, and it walked back one
#: commit per later commit until it pointed at a tree where the file was already gone, turning a
#: real non-vacuity proof into a false one. Caught by running the full suite pass, not by reading.
#: Pinning the commit is the discipline every predecessor package record already uses.
RUN54_PREDELETION_COMMIT = "bf36ef6"

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


# ------------------------------------------------------------------ GATE 8: one arithmetic source

print("=" * 78)
print("GATE 8. Browser and server parity: one arithmetic source, and only one")
print("=" * 78)

index_html = (ROOT / "index.html").read_text(encoding="utf-8")
for f in ("sim.js", "simulations.js", "categories.js"):
    check(f'assets/js/{f}' not in index_html,
          f"the participant application does not load {f}")

# RUN 54 RECONCILIATION. `research/deepdive.html` and `assets/js/deepdive.js` were DELETED
# on the owner's ruling at section 8 of the Run 54 order. The check below asserted that the
# browser instruments were CONFINED to that one route. With the route gone the same
# guarantee is STRONGER and is asserted as such: no served route loads them at all. The
# check is not deleted and not weakened -- its subject moved from 'confined to one page'
# to 'reached by no page', which is the stricter of the two. NON-VACUITY: both files exist
# at the prior commit, asserted against git rather than assumed.
_deep_gone = not (ROOT / "research" / "deepdive.html").exists()
_deep_existed = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e",
                                f"{RUN54_PREDELETION_COMMIT}:research/deepdive.html"], capture_output=True).returncode == 0
check(_deep_gone and _deep_existed,
      "the researcher deep dive is GONE, so the algorithm-version guard it loaded has no page "
      "left to protect: no served route runs browser arithmetic at all",
      f"deleted={_deep_gone} existed_at_bf36ef6={_deep_existed}")
guard = (ROOT / "assets" / "js" / "client_algorithm_version.js").read_text(encoding="utf-8")
check("simulation_version" in guard,
      "and the guard compares the client stamp against the stored simulation version")

#: Every live participant and researcher surface that could display module arithmetic, and what
#: each of them reads. Inventoried by name so a new surface has to be added here deliberately.
SURFACES = {
    "index.html": "server-stored results through projectresults",
    "assets/js/detail.js": "server-stored results through projectresults",
    "assets/js/signals.js": "server-stored results through projectresults",
    "assets/js/taxonomy.js": "server-stored results through projectresults",
    "assets/js/decision-ui.js": "server-stored results through projectresults",
}
#: RUN 54. `research/deepdive.html` was the sixth entry -- "historical client artefacts, behind
#: the version guard". It is DELETED, so it is no longer a surface and the inventory says so. The
#: entry is not silently dropped: the check below asserts it is GONE and that it EXISTED at the
#: prior commit, so the inventory's count of live surfaces falls by one for a reason on the
#: record rather than by an edit nobody has to justify.
RETIRED_SURFACES = {
    "research/deepdive.html": "DELETED by Run 54 on the owner's ruling at section 8",
}
for name in SURFACES:
    check((ROOT / name).exists(), f"inventoried surface exists: {name}")
for name in RETIRED_SURFACES:
    _was = subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", f"{RUN54_PREDELETION_COMMIT}:{name}"],
                          capture_output=True).returncode == 0
    check(not (ROOT / name).exists() and _was,
          f"retired surface is gone and was present at the prior commit: {name}",
          f"exists_now={(ROOT / name).exists()} existed_at_bf36ef6={_was}")

# No live participant asset may call the historical client arithmetic without the opt-in.
def strip_comments(src: str) -> str:
    """
    Comments naming a call are not calls. A scan that counts them reports a defect that is not
    there, which is exactly the class of false red this programme has been burned by, so the
    block and line comments come out before anything is matched.
    """
    src = re.sub(r"/\*.*?\*/", "", src, flags=re.S)
    return "\n".join(re.sub(r"//.*$", "", ln) for ln in src.splitlines())


for name in ("detail.js", "signals.js", "taxonomy.js", "app.js", "decision-ui.js"):
    src = strip_comments((ROOT / "assets" / "js" / name).read_text(encoding="utf-8"))
    calls = [m for m in re.finditer(r"LinSim\.\w+|LinSimulations\.\w+", src)]
    for m in calls:
        window = src[max(0, m.start() - 1200):m.start()]
        # Two forms of gate exist and both are Run 11's, so both are accepted and named:
        # the client-analytics opt-in the application never sets, and the explicit refusal
        # that returns when the retired model file is absent. What is NOT accepted is a call
        # with neither, which is the ReferenceError Run 11 found on a live call site.
        gated = ("LIN_ALLOW_CLIENT_ANALYTICS" in window
                 or re.search(r"if \(!window\.LinSim\w*\)", window))
        check(bool(gated),
              f"{name}: the call to {m.group(0)} is gated, by the opt-in or by an explicit "
              f"refusal when the retired model file is absent",
              src[max(0, m.start() - 90):m.start() + 40].replace("\n", " "))
    if not calls:
        check(True, f"{name}: no call into the historical client arithmetic at all")

check("LIN_ALLOW_CLIENT_ANALYTICS" not in index_html,
      "and the application itself never sets the opt-in")

# ------------------------------------------------------------------ GATE 9: governance

print("=" * 78)
print("GATE 9. Defensibility and governance")
print("=" * 78)

from app.simulation.registry import CORE_VOTING_MODULES, DISABLED_CONCEPT_ONLY  # noqa: E402
from app.simulation.fusion import governed_status_semantics, normalise_status  # noqa: E402



check(set(CORE_VOTING_MODULES) == {"A1.7", "A1.8"},
      "the voting set is exactly the two cost lineage modules", str(sorted(CORE_VOTING_MODULES)))
check(len(DISABLED_CONCEPT_ONLY) == 8,
      "the eight concept-only modules are still disabled", str(len(DISABLED_CONCEPT_ONLY)))
BUCKET5 = ("A3.1", "A5.1")
for mid in BUCKET5:
    check(mid not in CORE_VOTING_MODULES, f"Bucket-5 module {mid} does not vote")
check(all(normalise_status(s) is not None for s in ("Green", "Yellow", "Amber", "Red")),
      "the one place the status vocabulary is recognised still recognises it")

sem = governed_status_semantics({"A1": {"status": "Red", "conflict": 0.0, "group": "A",
                                        "module_count": 2,
                                        "contributes_to_project_status": True}}, 0.0)
check(sem.get("project_status_label") == "Cost Recovery Status",
      "the governed status label is Cost Recovery Status", str(sem.get("project_status_label")))
check(sem.get("project_conflict_state") == "NOT_ESTIMABLE_SINGLE_LINEAGE",
      "the one-lineage conflict semantics are unchanged", str(sem.get("project_conflict_state")))
check(sem.get("project_conflict") is None, "and no conflict coefficient is published")

# The generated defensibility evidence must still be byte-identical to what the registry says.
#
# RUN 22 FIXED A REAL SIDE EFFECT HERE, FOUND BY THE NEW FREEZE GUARD. This check used to invoke
# the generator in its DEFAULT mode, which WRITES assets/js/ds_defensibility_evidence.js -- a
# served production file -- and then compared the file to what it had been before. When the two
# agree, as they do on a healthy tree, the write is invisible and the check looks harmless. When
# they DISAGREE the suite reports the disagreement correctly and then LEAVES PRODUCTION
# OVERWRITTEN, because nothing restores it.
#
# Run 22's guard-mutation campaign hit exactly that. A deliberate mutation of the registry was
# reverted, but this suite had already rewritten the generated asset from the mutated registry,
# so the mutation survived in a file the campaign never touched. The new production-tree guard
# caught it -- which is the most convincing non-vacuity evidence in this run, because it caught a
# real unintended mutation rather than a staged one.
#
# The generator has always supported --stdout, and test_run11_defensibility_claims.py already
# uses it that way. The check is IDENTICAL in meaning -- regenerating from the registry must
# reproduce the committed file byte for byte -- and now has no side effect on the production tree.
# A test suite must not be able to modify the thing the freeze is protecting.
EVIDENCE_JS = "assets/js/ds_defensibility_evidence.js"
committed = (ROOT / EVIDENCE_JS).read_text(encoding="utf-8")
gen = subprocess.run([sys.executable, "tools/build_run11_defensibility_evidence.py", "--stdout"],
                     cwd=str(ROOT), capture_output=True, text=True)
check(gen.returncode == 0, "the defensibility evidence generator runs", gen.stderr[-160:])
check(gen.stdout == committed,
      "and regenerating it from the registry reproduces the committed file byte for byte")
check((ROOT / EVIDENCE_JS).read_text(encoding="utf-8") == committed,
      "and this check did not itself rewrite the production file it is checking")

# Nothing anywhere may claim a module has been validated.
banned = re.compile(r"has been validated|is validated|fully validated|empirically calibrated",
                    re.I)
for name in ("assets/js/ds_defensibility_evidence.js", "assets/js/ds_defensibility_data.js"):
    text = (ROOT / name).read_text(encoding="utf-8")
    check(not banned.search(text), f"no unsupported validation claim in {name}",
          str((banned.search(text) or [None]) and (banned.search(text).group(0)
                                                   if banned.search(text) else "")))

# Category 9 must never be described as validation or calibration, anywhere it is defined.
qual = (ROOT / "server" / "app" / "simulation" / "qualification.py").read_text(encoding="utf-8")
for word in ("validated", "calibrated", "empirical validation", "data quality score",
             "quality score", "confidence score"):
    check(word not in qual.lower(),
          f"the qualification object is nowhere described as '{word}'")
check("QUALIFICATION_VERSION" in qual, "and it carries its own version stamp")

# ------------------------------------------------------------------ GATE 10: separation

print("=" * 78)
print("GATE 10. Synthetic and operational separation")
print("=" * 78)

pkg = ROOT / "research_fixtures" / "synthetic" / "OG-SYNTH-0.3"
check(pkg.is_dir(), "the approved synthetic package is present", str(pkg))
importer = ROOT / "server" / "tests" / "synthetic_fixtures" / "importers"
imp_text = "\n".join(p.read_text(encoding="utf-8", errors="ignore")
                     for p in importer.glob("*.py"))
check("SYNTHETIC_RESEARCH_FIXTURE" in imp_text,
      "the fixture importer still requires data_origin = SYNTHETIC_RESEARCH_FIXTURE")
check("not_for_empirical_validation" in imp_text,
      "and still requires not_for_empirical_validation")
for forbidden in ("DATABASE_URL", "sessionmaker", "requests.", "httpx."):
    check(forbidden not in imp_text,
          f"the fixture importer holds no {forbidden}: it cannot reach operational storage")

# No production module and no production route may read the research fixtures.
prod = list((ROOT / "server" / "app").rglob("*.py"))
leaks = [str(p.relative_to(ROOT)) for p in prod
         if "research_fixtures" in p.read_text(encoding="utf-8", errors="ignore")
         or "synthetic_fixtures" in p.read_text(encoding="utf-8", errors="ignore")]
check(not leaks, "no production module reads the research or synthetic fixtures", str(leaks))

total = len(results)
passed = sum(1 for ok, _, _ in results if ok)
print()
for ok, label, detail in results:
    if not ok:
        print(f"FAILED: {label} {detail}")
print(f"RESULT: {passed}/{total} checks passed")
sys.exit(0 if passed == total else 1)
