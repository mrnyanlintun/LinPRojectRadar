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
    _map_body = dd.split("const CAT_FROM_MODULE = {", 1)[1].split("\n  };", 1)[0]
    _mapped = {k.encode().decode("unicode_escape")
               for k in re.findall(r'"([^"]+)":\s*"', _map_body)}
    print(f"    call sites: {len(_keys)}    mapped keys: {len(_mapped)}")
    check(len(_keys) == 77, "seventy-seven call sites pass a key", str(len(_keys)))
    check(not (_keys - _mapped),
          "AND EVERY ONE OF THEM RESOLVES TO AN EXPLICIT LABEL: no key reaches the neutral "
          "fallback, so ruling 3's exception list at 5.2 item 4 is EMPTY",
          str(sorted(_keys - _mapped)))
    check(not (_mapped - _keys),
          "and the map holds no key no call site passes, so it is not padded to pass this check",
          str(sorted(_mapped - _keys)))
    _labels = set(re.findall(r'":\s*"([^"]+)"', _map_body))
    _bad = sorted(l for l in _labels
                  if re.search(r"\d|Cat\s|&|—|–", l))
    check(not _bad,
          "and not one label carries a number, an identifier, an ampersand, an em dash or an "
          "en dash", str(_bad))
    print(f"    the {len(_labels)} distinct labels: {sorted(_labels)}")
    _v32_map = dd32.split("const CAT_FROM_MODULE = {", 1)[1].split("\n  };", 1)[0]
    check(len(re.findall(r'"[^"]+":\s*"', _v32_map)) == 19,
          "and the v32 map really did hold only nineteen keys, so the extension is a real "
          "change", str(len(re.findall(r'"[^"]+":\s*"', _v32_map))))

    print()
    print("4. NOT ONE MODULE BUCKETS DIFFERENTLY (S6.5, STOP CONDITION 9.4)")
    print("-" * 94)
    _num = dd.split("CAT_NUM_FROM_MODULE = {", 1)[1].split("};", 1)[0]
    _num32 = dd32.split("CAT_NUM_FROM_MODULE = {", 1)[1].split("};", 1)[0]
    check(_num == _num32,
          "THE GROUPING MAP IS BYTE-IDENTICAL TO v32. Run 48 separated it from the displayed "
          "text precisely so labels could change without moving panels, and this run did not "
          "touch it")
    _bucket_fn = dd.split("function catBucket(num)", 1)[1].split("\n  }", 1)[0]
    _bucket_fn32 = dd32.split("function catBucket(num)", 1)[1].split("\n  }", 1)[0]
    check(_bucket_fn == _bucket_fn32,
          "and the function that derives a bucket for an unmapped key is byte-identical too, so "
          "no dotted key can have moved either")

    print()
    print("5. decision-ui.js MOVED, AND THE DELTA IS COMMENTS AND NOTHING ELSE (RULING 4)")
    print("-" * 94)

    def strip_comments(t: str) -> str:
        return "\n".join(ln for ln in t.splitlines() if not ln.lstrip().startswith("//"))

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
    _tax = text("assets/js/taxonomy.js")
    check(_tax.splitlines()[285] == git_text("assets/js/taxonomy.js",
                                             V32_COMMIT).splitlines()[285],
          "assets/js/taxonomy.js:286 is byte-identical to v32")
    for rel in ("assets/js/app.js", "assets/js/categories.js", "assets/js/neural_flow.js",
                "assets/js/taxonomy.js"):
        check(text(rel) == git_text(rel, V32_COMMIT),
              f"{rel} is byte-identical to v32 in its entirety, so no marker in it can have "
              f"moved")

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
                    if hashlib.sha256((ROOT / f).read_bytes()).hexdigest() != _v17.get(f))
    check(_moved == ["assets/js/decision-ui.js", "assets/js/deepdive.js"],
          "exactly two sequence-bearing files moved since v17, and they are the two the owner "
          "authorised", str(_moved))
    check(sorted(PP.V17_TO_V18_SEQUENCE_EXCEPTION) == _moved,
          "and both are DECLARED BY NAME as the exception rather than excused by widening the "
          "comparison", str(PP.V17_TO_V18_SEQUENCE_EXCEPTION))
    _still = sorted(set(PP.SEQUENCE_BEARING_FILES) - set(_moved))
    check(len(_still) == 4
          and all(hashlib.sha256((ROOT / f).read_bytes()).hexdigest() == _v17[f]
                  for f in _still),
          "and the other four are byte for byte identical to v17", str(_still))

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
    check(re.search(r'num: "D1\.1"', dd) is not None
          and "${esc(m.num)}" not in dd,
          "and the CAT8_MODULES `num` field survives in the data while NOTHING interpolates it "
          "into the DOM any more, which is why it is a constant and not a label")

    print()
    print("10. GUARANTEE 1 IS NOT MET, AND THAT IS STATED RATHER THAN DRESSED UP")
    print("-" * 94)
    _app = text("assets/js/app.js")
    check('<span class="cat-mod-num">${esc(m.num)}</span>' in _app
          and '<span class="cat-row-num" style="color:${esc(cat.color)}">${esc(cat.num)}</span>'
          in _app,
          "assets/js/app.js STILL RENDERS a module identifier and a category identifier on the "
          "Categories page. This run was not ordered to correct them, both are read from the "
          "GENERATED taxonomy in categories.js, and correcting them means changing "
          "taxonomy_authority.json and regenerating. REPORTED, NOT CORRECTED")
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
