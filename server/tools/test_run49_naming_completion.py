#!/usr/bin/env python3
"""
RUN 49. THE COMPLETION OF THE NAMING CORRECTION.

Section 6 of the Run 49 order, everything that can be established without a browser. The
rendered-DOM half is drive_run49_browser.py and is not duplicated here.

A RAISE IS A FAILURE AND ITS TRACEBACK IS PRINTED. Run 48 recorded that a suite wrapping its
body in try/finally with sys.exit in the finally swallows its own traceback and prints a clean
RESULT line one check short. This file has an `except BaseException` arm for exactly that.
"""
from __future__ import annotations

import hashlib
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(HERE))

PASSED = 0
FAILED = 0
_fail: list[str] = []

#: The commit `main` stood at when this run began: the Run-48 merge, stamp sim-2026.08-v32.
V32_COMMIT = "5838a23"

#: The commit `main` stood at when RUN 49 FINISHED: the Run-49 merge, stamp sim-2026.08-v33.
#: RUN 51 NOTE. This suite is the record of what RUN 49 changed. Its "after" side is therefore
#: Run 49's own tree, not whatever tree it happens to run in: a later run that legitimately
#: edits the same file must not turn a historical record red, and reading the live tree here
#: would have exactly that effect. The checks below that compare a byte-identity or a package
#: checksum are re-anchored to V33_COMMIT. The checks that assert the CURRENT state of the code
#: -- sections 3, 4 and 10 -- deliberately still read the live tree.
V33_COMMIT = "ad4f614"


def check(ok, label, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        _fail.append(label)
        print(f"  ****  {label}" + (f"   [{detail}]" if detail else ""))
    return bool(ok)


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def git_text(rel: str, commit: str) -> str:
    return subprocess.run(["git", "show", f"{commit}:{rel}"], cwd=ROOT,
                          capture_output=True, check=True).stdout.decode("utf-8")


def rendered_lines(rel: str):
    """
    Every line of a served file that is NOT a comment. Section 2 of the order excludes comments
    and non-displayed code constants from the naming authority, so a sweep that counted them
    would report sites the authority does not govern.
    """
    out = []
    for i, ln in enumerate(text(rel).splitlines(), 1):
        st = ln.strip()
        if st.startswith("//") or st.startswith("*") or st.startswith("/*"):
            continue
        code = ln.split("//", 1)[0] if "//" in ln else ln
        out.append((i, code))
    return out


try:
    print("=" * 94)
    print("RUN 49: THE COMPLETION OF THE NAMING CORRECTION")
    print("=" * 94)

    dd = text("assets/js/deepdive.js")
    dd32 = git_text("assets/js/deepdive.js", V32_COMMIT)
    det = text("assets/js/detail.js")
    det32 = git_text("assets/js/detail.js", V32_COMMIT)
    du = text("assets/js/decision-ui.js")
    du32 = git_text("assets/js/decision-ui.js", V32_COMMIT)

    print()
    print("1. EVERY SITE THE ORDER NAMES AT 5.1, CORRECTED, AND PROVED PRESENT TO CORRECT")
    print("-" * 94)
    SITES = [
        ('the ten group headers', '<span class="mod-mono">Cat ${n}</span>'),
        ('the sentence naming the governance module', 'The classification feeds Cat 8.1'),
        ('the metric box label', 'metricBox("Agrees with Cat 6.1"'),
        ('the three summary sentences', 'agree with the Cat 6.1 baseline'),
        ('the two act-on sentences', 'Act on the Cat 8.1 recommendation'),
        ('the comparison panel heading',
         'Synthesis Methods Comparison: Cat 6.1 & Cat 7.1–7.9'),
        ('the comparison note', 'Conservative dominance (Cat 6.1) is the governance baseline'),
        ('the Signal Stack banner', 'Cat 1–Cat 3 modules are quantitative signal generators'),
    ]
    for label, needle in SITES:
        check(needle in dd32 and needle not in dd,
              f"deepdive.js: {label} is corrected, and the retired text really was there to "
              f"correct", f"in v32: {needle in dd32}; in tree: {needle in dd}")
    check("a program director does not think in Cat 1-12" in det32
          and "a program director does not think in Cat 1-12" not in det,
          "detail.js: the executive brief prompt no longer names the retired scheme to the model")
    check("Do NOT print any module identifier or category number" in det,
          "AND THE GUARDRAIL SURVIVES: the model is still told not to print an identifier. The "
          "sentence was rewritten, not deleted, because deleting it would remove a guard")
    check('cs("d-docsignals", "Documents & Extracted Signals"' in det32
          and 'cs("d-docsignals", "Documents and Extracted Signals"' in det
          and 'cs("d-docsignals", "Documents & Extracted Signals"' not in det,
          "detail.js: the document section title uses the word 'and', per ruling 2")

    print()
    print("2. THREE FURTHER LIVE INSTANCES NO ORDER NAMED, FOUND BY THIS RUN'S OWN SWEEP")
    print("-" * 94)
    EXTRA = [
        ('the comparison table row prefix', '<td class="dd-cmp-mod">Module ${e.num}:'),
        ('the comparison table agreement column header', '<th>Agrees with M09</th>'),
        ('the Portfolio Health module headings', '<b>${esc(m.num)} ${esc(m.name)}</b>'),
    ]
    for label, needle in EXTRA:
        check(needle in dd32 and needle not in dd,
              f"deepdive.js: {label} carried a module identifier into rendered text and is "
              f"corrected", f"in v32: {needle in dd32}; in tree: {needle in dd}")

    print()
    print("3. THE PANEL LABEL MAP COVERS EVERY KEY THE CALL SITES PASS (S6.4)")
    print("-" * 94)
    _keys = set()
    for m in re.finditer(r'\bpanel\("([^"]+)"', dd):
        _keys.add(m.group(1))
    _keys.discard("XX")
    # RUN 51, RULINGS 5 AND 6. Run 49 kept TWO maps -- CAT_FROM_MODULE for the label and
    # CAT_NUM_FROM_MODULE for the bucket -- and asserted the second was byte-identical to v32
    # because Run 49 was forbidden to move a panel. Ruling 5 ORDERS panels to move, and ruling 6
    # orders the bucket bound to be derived from the taxonomy. The two maps are now ONE table of
    # category KEYS, from which the label and the bucket are BOTH derived, so they cannot
    # disagree. Every check below is the same claim restated against that table. None is deleted.
    _map_body = dd.split("const CAT_KEY_FROM_MODULE = {", 1)[1].split("\n  };", 1)[0]
    _mapped = {k.encode().decode("unicode_escape")
               for k in re.findall(r'"([^"]+)":\s*"', _map_body)}
    print(f"    call sites: {len(_keys)}    mapped keys: {len(_mapped)}")
    check(len(_keys) == 78,
          "seventy-eight call sites pass a key: seventy-seven, plus the panel ruling 3 split the "
          "eight-module compliance panel into", str(len(_keys)))
    check(not (_keys - _mapped),
          "AND EVERY ONE OF THEM RESOLVES TO A CATEGORY IN THE CURRENT TAXONOMY: no key reaches "
          "the neutral fallback", str(sorted(_keys - _mapped)))
    check(not (_mapped - _keys),
          "and the map holds no key no call site passes, so it is not padded to pass this check",
          str(sorted(_mapped - _keys)))
    _values = set(re.findall(r'":\s*"([^"]+)"', _map_body))
    check(all(re.fullmatch(r"[A-D]\d", v) for v in _values),
          "and every VALUE is a category key, not a label and not a bucket number: the thing a "
          "participant reads is derived from the taxonomy at render time and is not in this file "
          "at all", str(sorted(_values)))
    # RUN 52, RULING 3: catLabel's parameter was renamed from `num` to `moduleId` -- one name
    # for the module identifier on both sides of the wire. THE CHECK IS UNCHANGED: it still
    # requires the label to be the category NAME read from the loaded taxonomy. Only the
    # parameter name it looks for moved. Nothing was weakened and no check was deleted.
    _cl = dd.split("function catLabel(moduleId)", 1)[1].split("\n  }", 1)[0]
    check("catLabel" in dd and "CAT_KEY_FROM_MODULE[String(moduleId).trim()]" in _cl
          and "(cat && cat.name)" in _cl,
          "and the label a panel renders is the category's NAME read from the loaded taxonomy, "
          "so it can carry no number, no identifier, no ampersand and no dash by construction")
    print(f"    the {len(_values)} distinct category keys: {sorted(_values)}")
    _v32_map = dd32.split("const CAT_FROM_MODULE = {", 1)[1].split("\n  };", 1)[0]
    check(len(re.findall(r'"[^"]+":\s*"', _v32_map)) == 19,
          "and the v32 map really did hold only nineteen keys, so the extension is a real "
          "change", str(len(re.findall(r'"[^"]+":\s*"', _v32_map))))

    print()
    print("4. THE BUCKETS MOVED, AND THEY MOVED EXACTLY WHERE RULING 5 ORDERS")
    print("-" * 94)
    _prior_dd = subprocess.run(["git", "show", "ad4f614:assets/js/deepdive.js"], cwd=str(ROOT),
                               capture_output=True, text=True, encoding="utf-8").stdout
    check("CAT_NUM_FROM_MODULE" in _prior_dd and "CAT_NUM_FROM_MODULE" not in dd,
          "the separate grouping map that Run 49 froze at v32 IS GONE, and it really was there "
          "at ad4f614, so this is not a vacuous absence")
    _bucket_fn = dd.split("function catBucket(moduleId)", 1)[1].split("\n  }", 1)[0]
    check("findIndex" in _bucket_fn and "projectCatList()" in _bucket_fn
          and not re.search(r"return\s+m\s*\?\s*m\[1\]", _bucket_fn),
          "and the bucket is now the category's POSITION in the in-service project-level "
          "taxonomy, derived, with no literal and no fallback that parses a retired number out "
          "of a key", _bucket_fn.strip()[:200])
    _loop = re.search(r"for \(let n = 1; n <= ([^;]+);", dd)
    check(_loop is not None and _loop.group(1).strip() == "projectCats.length",
          "and RULING 6 IS MET IN THE CODE: the grouping loop runs to the number of project-level "
          "categories the taxonomy holds, not to a literal ten",
          _loop.group(1) if _loop else "no loop found")
    check("for (let n = 1; n <= 10; n++)" in _prior_dd,
          "and the loop really did run to a literal ten at ad4f614, so widening it is a real "
          "change and not a check written around what was already there")
    # The seven mis-filings ruling 5 names, asserted one by one against the new table.
    _tbl = {k.encode().decode("unicode_escape"): v for k, v in
            re.findall(r'"([^"]+)":\s*"([^"]+)"', _map_body)}
    for _panel, _want, _why in [
            ("03", "A4", "old 1.3, an alias of 4.1"),
            ("3.2", "A5", "old 3.2, an alias of 5.1"),
            ("09", "B1", "old 6.1"), ("6.1", "B1", "old 6.1"), ("6.2", "B1", "old 6.2"),
            ("6.3", "B1", "old 6.3"), ("6.4", "B1", "old 6.4"),
            ("7.1", "B2", "old 7.1"), ("7.2 to 7.8", "B2", "old 7.2 to 7.8"),
            ("7.9 to 7.20", "B2", "old 7.9 to 7.20"),
            ("19", "B3", "old 8.1"), ("8.1", "B3", "old 8.1"),
            ("8.2 to 8.5", "B3", "old 8.2 to 8.5, the regulatory half of the split panel"),
            ("8.6 to 8.9", "A6", "old 8.6 to 8.9, the delivery-quality half of the split panel"),
            ("9.1", "C1", "old 9.1"), ("9.2 to 9.7", "C1", "old 9.2 to 9.7"),
            ("08", "A5", "old 8, system dynamics"),
            ("04", "A2", "old 4"), ("05", "A2", "old 5"), ("06", "A2", "old 6"),
            ("07", "A3", "old 7")]:
        check(_tbl.get(_panel) == _want,
              f"panel {_panel} is filed under {_want}, which is where {_why} belongs in the "
              f"current taxonomy", f"{_panel} -> {_tbl.get(_panel)}")

    print()
    print("5. decision-ui.js MOVED, AND THE DELTA IS COMMENTS AND NOTHING ELSE (RULING 4)")
    print("-" * 94)

    def strip_comments(t: str) -> str:
        return "\n".join(ln for ln in t.splitlines() if not ln.lstrip().startswith("//"))

    # Anchored to Run 49's own tree: this is Run 49's claim about Run 49's delta.
    du = git_text("assets/js/decision-ui.js", V33_COMMIT)
    check(du != du32, "decision-ui.js moved")
    check(strip_comments(du) == strip_comments(du32),
          "AND WITH EVERY WHOLE-LINE COMMENT REMOVED THE TWO VERSIONS ARE IDENTICAL: not one "
          "byte of executable text changed")
    check(du.count("period: 1") == du32.count("period: 1") == 3,
          "the three period literals are still there, unchanged in number, exactly as ruling 4 "
          "orders", f"{du.count('period: 1')} vs {du32.count('period: 1')}")
    _rec = "documents._resolve_period derives the period from the research assignment"
    check(du.count("RUN 49, ruling 4") == 2,
          "and the override is recorded at both call-site blocks that carry the literals",
          str(du.count("RUN 49, ruling 4")))
    check("a request stating 1 returned 3" in du,
          "and the record cites the EXECUTED evidence rather than asserting the claim")

    print()
    print("6. THE COMMENT MARKERS OF SECTION 2 ARE UNCHANGED, ASSERTED PER FILE BY CONTENT")
    print("-" * 94)
    MARKERS = {
        "assets/js/app.js": ('expands the per-module list. Cat 8 (Governance, ex-Cat 9) is open by',),
        "assets/js/categories.js": ("(A4.1 and A5.1). See p0-baseline/MODULE_TAXONOMY.md.",),
        "assets/js/deepdive.js": ('Portfolio Health (ex-"Cat 8") is portfolio-scale, so it is NOT part of the',
                                  'Portfolio Health (ex-"Cat 8" ML/AI) is portfolio-scale, not single-project'),
        "assets/js/neural_flow.js": ('Every document row the old array sent to "Cat 8" was rendered',),
        "assets/js/taxonomy.js": (None,),
    }
    for rel, needles in MARKERS.items():
        for n in needles:
            if n is None:
                continue
            check(n in text(rel), f"{rel}: the comment marker is unchanged", n[:60])
    _tax = git_text("assets/js/taxonomy.js", V33_COMMIT)
    check(_tax.splitlines()[285] == git_text("assets/js/taxonomy.js",
                                             V32_COMMIT).splitlines()[285],
          "assets/js/taxonomy.js:286 was byte-identical to v32 across Run 49")
    for rel in ("assets/js/app.js", "assets/js/categories.js", "assets/js/neural_flow.js",
                "assets/js/taxonomy.js"):
        check(git_text(rel, V33_COMMIT) == git_text(rel, V32_COMMIT),
              f"{rel} was byte-identical to v32 in its entirety across Run 49, so no marker in "
              f"it can have moved in that run")
    # RUN 51 moved three of those four under rulings 2 and 4. The protected markers are still
    # asserted present in the LIVE tree by the MARKERS loop above; what is anchored to Run 49
    # here is Run 49's claim about Run 49.

    print()
    print("7. THE POPULATIONS AND THE VOTERS, DERIVED (S6.12, S6.13)")
    print("-" * 94)
    from app.simulation.registry import (  # noqa: E402
        CORE_VOTING_MODULES, registry_index, service_index)
    check(len(service_index()) == 63, "modules in service is 63, called live",
          str(len(service_index())))
    check(len(registry_index()) == 101, "registry total is 101, called live",
          str(len(registry_index())))
    check(sorted(CORE_VOTING_MODULES) == ["A1.7", "A1.8"],
          "voting is exactly two, A1.7 and A1.8", str(sorted(CORE_VOTING_MODULES)))

    print()
    print("8. EXACTLY TWO SEQUENCE-BEARING FILES MOVED (S6.14, STOP CONDITION 9.5)")
    print("-" * 94)
    import participant_packages as PP  # noqa: E402
    _v17 = {}
    for ln in text("code_audit/run48_participant_package_v17_checksums.sha256").splitlines():
        if re.match(r"^[0-9a-f]{64}  ", ln):
            h, p = ln.split("  ", 1)
            _v17[p] = h
    _moved = sorted(f for f in PP.SEQUENCE_BEARING_FILES
                    if hashlib.sha256(git_text(f, V33_COMMIT).encode("utf-8")).hexdigest()
                    != _v17.get(f))
    check(_moved == ["assets/js/decision-ui.js", "assets/js/deepdive.js"],
          "exactly two sequence-bearing files moved between v17 and v18, and they are the two "
          "the owner authorised for RUN 49", str(_moved))
    check(sorted(PP.V17_TO_V18_SEQUENCE_EXCEPTION) == _moved,
          "and both are DECLARED BY NAME as the exception rather than excused by widening the "
          "comparison", str(PP.V17_TO_V18_SEQUENCE_EXCEPTION))
    _still = sorted(set(PP.SEQUENCE_BEARING_FILES) - set(_moved))
    check(len(_still) == 4
          and all(hashlib.sha256(git_text(f, V33_COMMIT).encode("utf-8")).hexdigest() == _v17[f]
                  for f in _still),
          "and the other four were byte for byte identical to v17 at the end of Run 49",
          str(_still))

    print()
    print("9. THE SECOND SWEEP: WHAT STILL RENDERS THE RETIRED SCHEME, REPORTED NOT CLAIMED")
    print("-" * 94)
    _pat = re.compile(r"\bCat\s*\d|\bM0\d\b|\bD1\.\d")
    _survivors = []
    for rel in sorted(p.relative_to(ROOT).as_posix()
                      for p in (ROOT / "assets" / "js").glob("*.js")):
        for i, code in rendered_lines(rel):
            if _pat.search(code):
                _survivors.append(f"{rel}:{i}")
    print(f"    non-comment lines matching the retired scheme across assets/js: "
          f"{len(_survivors)}")
    for s in _survivors[:40]:
        print(f"      {s}")
    # THE DEEPDIVE SURVIVORS, EACH CLASSIFIED BY ITS OWN LINE CONTENT RATHER THAN EXCUSED.
    # Two kinds survive and neither is user-facing text under section 2 of the order: a
    # CONTINUATION LINE of a block comment (the sweep only skips lines that OPEN with a comment
    # marker, so an indented continuation is caught and has to be classified here), and the
    # `num:` field of CAT8_MODULES, which this run stopped rendering at the Portfolio Health
    # heading and which is now a matched-against constant with no reader that prints it.
    _dd_lines = dd.splitlines()
    _unexplained = []
    for s in [x for x in _survivors if x.startswith("assets/js/deepdive.js")]:
        n = int(s.split(":")[1])
        ln = _dd_lines[n - 1]
        if re.match(r'^\s*\{ mc: "[A-Za-z_]+",\s*num: "D1\.\d", name: ', ln):
            print(f"      {s}  CAT8_MODULES map entry, no longer rendered")
            continue
        # Inside a block comment: count the /* and */ that precede this line.
        head = "\n".join(_dd_lines[:n - 1])
        if head.count("/*") > head.count("*/"):
            print(f"      {s}  block-comment continuation line")
            continue
        _unexplained.append(s)
    check(not _unexplained,
          "IN deepdive.js EVERY SURVIVING MATCH IS EXPLAINED BY ITS OWN LINE: a block-comment "
          "continuation or a CAT8_MODULES map key that nothing prints any more. Not one is "
          "rendered text", str(_unexplained))
    # RUN 51, RULING 1. Run 49 kept CAT8_MODULES[].num as an unread constant and this check
    # recorded that it survived unrendered. Ruling 1 deleted the whole Portfolio Health flyout,
    # CAT8_MODULES with it, so the check is reconciled to the stronger claim: the field is gone
    # ENTIRELY, and it really was there at ad4f614, so the absence is not vacuous.
    _dd_prior = subprocess.run(["git", "show", "ad4f614:assets/js/deepdive.js"], cwd=str(ROOT),
                               capture_output=True, text=True, encoding="utf-8").stdout
    check(re.search(r'num: "D1\.1"', _dd_prior) is not None,
          "the CAT8_MODULES `num` field WAS present at ad4f614, so the absence check below is "
          "not vacuous")
    check(re.search(r'num: "D1\.\d"', dd) is None and "CAT8_MODULES" not in dd
          and "${esc(m.num)}" not in dd,
          "and the whole CAT8_MODULES table, its unread `num` field included, is gone from "
          "deepdive.js with the flyout that was its only reader")

    print()
    print("10. GUARANTEE 1 IS NOT MET, AND THAT IS STATED RATHER THAN DRESSED UP")
    print("-" * 94)
    _app = text("assets/js/app.js")
    # RUN 51, RULING 2. Run 49 recorded this as a defect it was not ordered to correct. It is
    # corrected: the two identifier chips are gone from app.js, and the field they read is no
    # longer called `num` anywhere -- it is `key`, which dispatches, while what renders is the
    # module's and the category's NAME. The check is reconciled, not deleted, and it is
    # non-vacuous because the same two spans are asserted to have been present at ad4f614.
    _app_prior = subprocess.run(["git", "show", "ad4f614:assets/js/app.js"], cwd=str(ROOT),
                                capture_output=True, text=True, encoding="utf-8").stdout
    check('<span class="cat-mod-num">${esc(m.num)}</span>' in _app_prior
          and '<span class="cat-row-num" style="color:${esc(cat.color)}">${esc(cat.num)}</span>'
          in _app_prior,
          "assets/js/app.js DID render a module identifier and a category identifier at "
          "ad4f614, so the correction below is not a check that passes vacuously")
    check('cat-mod-num' not in _app and 'cat-row-num' not in _app
          and '${esc(m.num)}' not in _app and '${esc(cat.num)}' not in _app,
          "and NEITHER RENDERS NOW: guarantee 1 is met at both sites, corrected in code rather "
          "than reported")
    _seq_dashes = {}
    for rel in PP.SEQUENCE_BEARING_FILES:
        n = len(re.findall(r"[—–]", text(rel)))
        if n:
            _seq_dashes[rel] = n
    print(f"    en/em dashes still in sequence-bearing files: {_seq_dashes}")
    check(set(_seq_dashes) - {"assets/js/deepdive.js", "assets/js/decision-ui.js"},
          "and en or em dashes remain in user-facing text inside sequence-bearing files this "
          "run has NO AUTHORITY TO MOVE, which is why guarantee 1 cannot be met inside stop "
          "condition 9.5", str(_seq_dashes))

except BaseException:
    import traceback
    traceback.print_exc()
    FAILED += 1
    _fail.append("the suite raised")
    print("  ****  the suite raised; counted as a failure")

print()
if _fail:
    print("FAILURES:")
    for f in _fail:
        print(f"  - {f}")
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
