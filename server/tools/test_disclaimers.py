"""
The live disclaimer text must equal its reviewable source, character for character.

WHY THIS EXISTS. The liability notices are approved wording. The approval is recorded in
DISCLAIMERS_DRAFT.md, and the text a user actually sees lives in index.html. Two copies of
approved legal text in two files is exactly the shape that drifts: someone tightens a sentence on
the live surface, the reviewed source still says the old thing, and nobody can say afterwards
which wording was approved. This check makes that divergence a red suite rather than a discovery.

WHAT IT DOES NOT DO. It does not judge the wording, and it cannot: a session may not extend or
strengthen liability language on its own judgement. It only asserts that what ships is what was
approved, and that both account types carry their own variant on every surface that shows one.

THE UPLOAD PANELS. index.html carries the sign-in notice and the footer as static HTML. The four
upload panels in signals.js and auditor.js are built as HTML strings at render time and cannot,
so they share one constant in assets/js/disclaimers.js. That constant is checked against the same
source here. It had already drifted before this check existed: the four panels carried wording
that matched neither each other nor the approved notice, because they were a surface the approval
did not originally cover.

Reads files only. No database, no server, no network.
"""

from __future__ import annotations

import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SOURCE = ROOT / "DISCLAIMERS_DRAFT.md"
LIVE = ROOT / "index.html"
SHARED = ROOT / "assets" / "js" / "disclaimers.js"
PANEL_FILES = (ROOT / "assets" / "js" / "signals.js",
               ROOT / "assets" / "js" / "auditor.js")

# Developer-facing pages that carry the approved attribution sentence in their own footer. They
# used to carry a fused attribution-plus-advisory sentence of their own invention, four copies of
# it, which is the same drift shape the upload panels had.
ATTRIBUTION_PAGES = (ROOT / "calibration" / "verify.html",
                     ROOT / "tools" / "export_lib.html",
                     ROOT / "tests.html",
                     ROOT / "assets" / "visualizations" / "pceif_neural_signal_flow.html")

# Wording retired on 2026-08-02 that must not come back on any surface. "the associated framework"
# asserted a framework exists; NAMING_AUTHORITY.md says there deliberately is none. The trademark
# symbol was dropped. The attribution title block read as though the university issued the notice.
RETIRED = (
    "Opus Gubernatio™",
    "the associated framework",
    "The George Washington University · Doctor of Engineering praxis research",
    "The School of Engineering and Applied Science of The George Washington University",
)

PASSED = 0
FAILED = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def norm(s: str) -> str:
    """Collapse whitespace so an HTML line wrap is not a text difference."""
    return re.sub(r"\s+", " ", s).strip()


def strip_tags(s: str) -> str:
    """Rendered text of an HTML fragment: drop tags, unescape entities, collapse whitespace."""
    return norm(html.unescape(re.sub(r"<[^>]+>", " ", s)))


def source_variants() -> dict[str, list[str]]:
    """
    The approved paragraphs, extracted from the numbered sections of the source file.

    Parsed rather than hardcoded, deliberately: a copy of the text in this file would be a third
    copy to drift, which is the very thing the check exists to prevent.
    """
    text = SOURCE.read_text(encoding="utf-8")
    out: dict[str, list[str]] = {}
    for key, heading in (("research", "## 1."), ("operational", "## 2."),
                         ("constant", "## 3.")):
        start = text.index(heading)
        rest = text[start + len(heading):]
        end = rest.find("\n## ")
        block = rest[:end] if end != -1 else rest
        # Blockquote lines only; a blank "> " line separates paragraphs.
        paras, current = [], []
        for line in block.splitlines():
            if line.startswith(">"):
                body = line[1:].strip()
                if body:
                    current.append(body)
                elif current:
                    paras.append(norm(" ".join(current)))
                    current = []
            elif current:
                paras.append(norm(" ".join(current)))
                current = []
        if current:
            paras.append(norm(" ".join(current)))
        # Markdown bold is presentation; the live text carries it as <strong>.
        out[key] = [p.replace("**", "") for p in paras]
    return out


def live_blocks(cls: str) -> list[str]:
    """Rendered text of every element in index.html carrying the given notice class."""
    doc = LIVE.read_text(encoding="utf-8")
    blocks = []
    for m in re.finditer(r'<(\w+)([^>]*\bclass="[^"]*\b' + re.escape(cls) + r'\b[^"]*"[^>]*)>', doc):
        tag = m.group(1)
        # Walk to the matching close tag, counting nested same-name tags.
        i, depth = m.end(), 1
        open_re = re.compile(r"<%s\b" % tag)
        close_re = re.compile(r"</%s>" % tag)
        while depth and i < len(doc):
            nxt_o = open_re.search(doc, i)
            nxt_c = close_re.search(doc, i)
            if not nxt_c:
                break
            if nxt_o and nxt_o.start() < nxt_c.start():
                depth += 1
                i = nxt_o.end()
            else:
                depth -= 1
                i = nxt_c.end()
        blocks.append(doc[m.end():i])
    return blocks


print("test_disclaimers - the live text equals its approved source")
print()

check(SOURCE.is_file(), "DISCLAIMERS_DRAFT.md present", str(SOURCE))
check(LIVE.is_file(), "index.html present", str(LIVE))
check(SHARED.is_file(), "assets/js/disclaimers.js present", str(SHARED))
if FAILED:
    print("\nRESULT: cannot run")
    sys.exit(1)

variants = source_variants()

print("\n1. The source parses into two variants of three paragraphs each")
for key in ("research", "operational"):
    check(len(variants[key]) == 3, f"{key} variant has 3 paragraphs",
          f"got {len(variants[key])}")
    check(all(len(p) > 40 for p in variants[key]), f"{key} paragraphs are non-trivial",
          str([len(p) for p in variants[key]]))

# A source that failed to parse would make every check below vacuously pass, so stop here.
if FAILED:
    print("\nRESULT: source did not parse; downstream checks would be vacuous")
    sys.exit(1)

print("\n2. Both surfaces carry each variant, and both are present")
for key, cls in (("research", "notice-research"), ("operational", "notice-operational")):
    blocks = live_blocks(cls)
    check(len(blocks) >= 2, f"{cls} appears on at least 2 surfaces (sign-in and footer)",
          f"found {len(blocks)}")

print("\n3. Every live paragraph matches the approved source verbatim")
for key, cls in (("research", "notice-research"), ("operational", "notice-operational")):
    blocks = live_blocks(cls)
    # Only the surfaces that carry the full notice: the upload-panel disclaimers in signals.js
    # and auditor.js use the same class but are a separate, shorter surface this file does not
    # govern. index.html carries the sign-in notice and the footer, and only those.
    for n, block in enumerate(blocks, 1):
        rendered = strip_tags(block)
        for p, para in enumerate(variants[key], 1):
            check(para in rendered,
                  f"{cls} surface {n} carries approved paragraph {p} verbatim",
                  para[:60] + "...")

print("\n4. Neither variant leaks the other's text")
# The research variant's synthetic-data sentence is exactly what must never reach an operational
# user: they upload real project documents by design, so the statement would be false for them.
SYNTHETIC = "All project data is synthetic."
for block in live_blocks("notice-operational"):
    check(SYNTHETIC not in strip_tags(block),
          "operational surface does not claim all project data is synthetic")
for block in live_blocks("notice-research"):
    check(SYNTHETIC in strip_tags(block) or "upload confidential" in strip_tags(block),
          "research surface keeps the restrictive text")

print("\n5. The approved text carries no em dash and no module id")
for key in ("research", "operational"):
    joined = " ".join(variants[key])
    check("—" not in joined, f"{key} variant has no em dash")
    check(not re.search(r"\b[ABCD]\d+\.\d+\b", joined), f"{key} variant has no module id")

print("\n6. The upload panels carry the same approved text, from one shared constant")
shared_src = SHARED.read_text(encoding="utf-8")
shared_norm = norm(shared_src)
for key in ("research", "operational"):
    for p, para in enumerate(variants[key], 1):
        # The shared constant stores the paragraph as a JS string literal. Its apostrophes are
        # plain, so a straight substring test on the normalised file is exact.
        check(para in shared_norm,
              f"disclaimers.js carries approved {key} paragraph {p} verbatim",
              para[:60] + "...")

# The panels must RENDER the shared constant, not their own copy of the words. A panel that
# reintroduced a literal notice would pass the check above and still ship divergent text.
for path in PANEL_FILES:
    src = path.read_text(encoding="utf-8")
    name = path.name
    check("LinDisclaimers.uploadNoticeHtml()" in src,
          f"{name} renders the shared notice")
    check("upload-disclaimer notice-research" not in src
          and "upload-disclaimer notice-operational" not in src,
          f"{name} carries no literal notice of its own",
          "a hardcoded upload-disclaimer block is present")
    # `${...}` only interpolates inside a template literal. In an ordinary quoted string it
    # ships to the user as the characters "${LinDisclaimers.uploadNoticeHtml()}". node --check
    # accepts both, so the delimiter is asserted here rather than assumed.
    for m in re.finditer(r"\$\{LinDisclaimers\.uploadNoticeHtml\(\)\}", src):
        before = src[:m.start()]
        ticks, i = 0, 0
        while i < len(before):
            if before[i] == "\\":
                i += 2
                continue
            if before[i] == "`":
                ticks += 1
            i += 1
        line = before.count("\n") + 1
        check(ticks % 2 == 1,
              f"{name}:{line} call site is inside a template literal (it interpolates)",
              "even backtick count means it would ship as literal text")

print("\n7. The shared constant is loaded before the files that use it")
index_src = LIVE.read_text(encoding="utf-8")
pos_shared = index_src.find('src="assets/js/disclaimers.js"')
check(pos_shared != -1, "index.html loads assets/js/disclaimers.js")
for path in PANEL_FILES:
    pos_user = index_src.find(f'src="assets/js/{path.name}"')
    check(pos_user != -1 and pos_shared != -1 and pos_shared < pos_user,
          f"disclaimers.js loads before {path.name}",
          f"shared at {pos_shared}, {path.name} at {pos_user}")

print("\n8. Section 3 parses into the attribution sentence and the copyright paragraph")
constant = variants["constant"]
check(len(constant) == 2, "section 3 has 2 blockquote paragraphs", f"got {len(constant)}")
ATTRIBUTION = next((p for p in constant if "George Washington" in p), "")
COPYRIGHT = next((p for p in constant if p.startswith("©")), "")
check(bool(ATTRIBUTION), "section 3 carries the university attribution sentence")
check(bool(COPYRIGHT), "section 3 carries the copyright paragraph")
# The three things the 2026-08-02 revision removed. Asserted against the SOURCE as well as the
# live surfaces, so reintroducing them by "fixing" the source is also a red suite.
check("is not a party to this notice" in ATTRIBUTION,
      "the attribution states the university is not a party to the notice")
check("does not endorse or warrant" in ATTRIBUTION,
      "the attribution states the university does not endorse or warrant the platform")
check("framework" not in COPYRIGHT, "the copyright no longer asserts an associated framework")
check("™" not in COPYRIGHT, "the copyright carries no trademark symbol")

if not ATTRIBUTION or not COPYRIGHT:
    print("\nRESULT: section 3 did not parse; downstream checks would be vacuous")
    sys.exit(1)

print("\n9. The live surfaces carry section 3 verbatim")
for cls, para, label in (("footer-copyright", COPYRIGHT, "copyright paragraph"),
                         ("footer-praxis", ATTRIBUTION, "attribution sentence")):
    blocks = live_blocks(cls)
    check(len(blocks) == 1, f".{cls} appears once in index.html", f"found {len(blocks)}")
    check(bool(blocks) and para in strip_tags(blocks[0]),
          f"the footer carries the approved {label} verbatim", para[:60] + "...")

# The sign-in box and the access-denied panel. Both used to carry their own short attribution, a
# middot line and a "GWU ... Praxis" line, each sitting under a liability disclaimer where it read
# as a signature block. Both now carry the same sentence as every other surface. .login-footnote
# is also used by unrelated expanders, so this counts the ones that carry it rather than requiring
# all of them to.
footnotes = [b for b in live_blocks("login-footnote") if ATTRIBUTION in strip_tags(b)]
check(len(footnotes) >= 2,
      "at least 2 .login-footnote surfaces carry the approved attribution sentence",
      f"found {len(footnotes)} (expected the sign-in box and the access-denied panel)")

print("\n10. The developer-facing pages carry the approved attribution sentence")
for path in ATTRIBUTION_PAGES:
    check(path.is_file(), f"{path.name} present", str(path))
    if path.is_file():
        check(ATTRIBUTION in strip_tags(path.read_text(encoding="utf-8")),
              f"{path.name} carries the approved attribution sentence verbatim")

print("\n11. No retired wording survives on any surface")
SURFACES = (LIVE, SHARED) + ATTRIBUTION_PAGES
for path in SURFACES:
    if not path.is_file():
        continue
    rendered = norm(path.read_text(encoding="utf-8"))
    for phrase in RETIRED:
        check(phrase not in rendered, f"{path.name} does not carry retired wording",
              phrase[:60])

print("\n12. The access-denied panel carries no liability notice of its own")
# It used to carry "Access restricted to authorized use. This platform is an academic
# proof-of-concept; no warranty is provided." That was a third variant, derived from neither
# approved section, switching on nothing, and shown BEFORE authentication, so an operational user
# who failed sign-in was told the platform is an academic proof of concept. It was removed rather
# than replaced: a person who has not signed in has uploaded nothing and needs no upload
# disclaimer. These checks are what stop it, or a substitute, coming back.
live_doc = LIVE.read_text(encoding="utf-8")
denied = re.search(r'<div id="lin-access-denied".*?\n  </div>', live_doc, re.S)
check(denied is not None, "the access-denied panel is still in index.html")
if denied:
    panel = denied.group(0)
    check("proof-of-concept" not in panel and "proof of concept" not in panel,
          "the retired one-line notice is gone from the panel")
    check('class="login-disclaimer"' not in panel,
          "and no .login-disclaimer paragraph replaced it")
    for para in variants["research"] + variants["operational"]:
        check(norm(para) not in strip_tags(panel),
              "no approved advisory variant was substituted into the panel either",
              para[:50])
    # The attribution DOES belong here and is approved for this surface. Asserting it stays is
    # what keeps the removal above from being over-applied to the whole panel.
    check(ATTRIBUTION in strip_tags(panel),
          "the approved attribution sentence is still on the panel")

print("\n13. The meta description quotes the standing description, and claims no domain")
meta = re.search(r'<meta name="description" content="([^"]*)"', live_doc)
check(meta is not None, "index.html has a meta description")
if meta:
    desc = norm(html.unescape(meta.group(1)))
    authority = (ROOT / "NAMING_AUTHORITY.md").read_text(encoding="utf-8")
    # The short form, parsed from the authority rather than copied here, for the same reason
    # source_variants() parses: a copy in this file is a copy that can drift.
    short = re.search(r"\*\*Short form, one sentence:\*\*\s*\n\s*\n((?:> .*\n)+)", authority)
    check(short is not None, "the authority still carries a short-form standing description")
    if short:
        want = norm(" ".join(l.lstrip("> ").rstrip() for l in short.group(1).splitlines()))
        check(desc == want, "the meta description is the short form verbatim", desc[:70])
    for claim in ("AEC", "capital program", "capital project", "public sector", "public-sector"):
        check(claim.lower() not in desc.lower(),
              f"the meta description does not assert a domain ({claim})", desc[:70])

print("\n14. The XLSX export carries the approved notice, and does not restate it")
EXPORT_JS = ROOT / "assets" / "js" / "export.js"
check(EXPORT_JS.is_file(), "export.js present")
if EXPORT_JS.is_file():
    ejs = EXPORT_JS.read_text(encoding="utf-8")
    check('book_append_sheet(wb, wsNotice, "Notice")' in ejs,
          "the workbook gets a Notice sheet")
    # SHEET ORDER IS DECIDED BY THE ORDER OF THE APPEND CALLS, so that is what is compared. An
    # earlier version of this check compared where the variable names first appear in the source,
    # which is a proxy for the thing that matters and not the thing itself: fault injection moved
    # the sheet without moving the declaration and the check stayed green.
    appends = re.findall(r'book_append_sheet\(wb,\s*\w+,\s*"([^"]+)"', ejs)
    check(appends[:1] == ["Notice"],
          "and it is appended first, so it is the sheet that opens", str(appends))
    check("LinDisclaimers" in ejs and "currentNotice" in ejs,
          "it takes the text from the shared approved constant")
    # The point of the shared constant: no fourth copy of approved legal text.
    for para in variants["research"] + variants["operational"] + [ATTRIBUTION, COPYRIGHT]:
        head = norm(para)[:60]
        check(head not in norm(ejs),
              "export.js does not restate the approved text itself", head[:50])

print("\n15. disclaimers.js and research_export.py carry section 3 verbatim")
shared_js = SHARED.read_text(encoding="utf-8")
for label, para in (("attribution", ATTRIBUTION), ("copyright", COPYRIGHT)):
    # Both files wrap these across source lines, so compare against the concatenated literal.
    joined = norm(re.sub(r'"\s*\+?\s*\n\s*"', "", shared_js))
    check(norm(para) in joined, f"disclaimers.js carries the approved {label} verbatim",
          para[:50])

EXPORT_PY = ROOT / "server" / "app" / "research_export.py"
check(EXPORT_PY.is_file(), "research_export.py present")
if EXPORT_PY.is_file():
    epy = EXPORT_PY.read_text(encoding="utf-8")
    joined_py = norm(re.sub(r'"\s*\n\s*"', "", epy))
    for para in variants["research"]:
        check(norm(para) in joined_py,
              "the research export carries the approved research variant verbatim", para[:50])
    for label, para in (("attribution", ATTRIBUTION), ("copyright", COPYRIGHT)):
        check(norm(para) in joined_py,
              f"the research export carries the approved {label} verbatim", para[:50])
    # The operational variant must NOT be there. build_rows filters to research accounts only, so
    # an operational branch would assert an export that cannot exist. If that filter is ever
    # relaxed, this check is the reminder that the notice decision has to be revisited.
    # Skip any operational paragraph that is CONTAINED IN a research one rather than only those
    # equal to one. The two variants share the "Analytical outputs are advisory..." sentence, so
    # an equality test lets a shared sentence be reported as an operational leak.
    for para in variants["operational"]:
        if any(norm(para) in norm(p) for p in variants["research"]):
            continue
        check(norm(para) not in joined_py,
              "and does not carry the operational variant, which cannot apply to it", para[:50])

print("\n16. Nothing claims the platform is, or has, a governance framework")
# NAMING_AUTHORITY.md: "There is deliberately no framework name... If you find yourself needing a
# framework name to describe what the platform does, describe what it does instead." The praxis
# outline contradicted its own lead: the lead said the contribution is empirical evidence "not a
# new governance framework", and three chapter descriptions below it said the framework is
# grounded, built as an artifact, and evaluated by practitioners.
#
# CITING SOMEONE ELSE'S FRAMEWORK IS FINE and must stay possible: the file legitimately references
# "Sargent's simulation V&V framework" and "the course's error framework". Those are possessive,
# so forbidding the bare definite article catches the platform's own claim without touching them.
DS = ROOT / "assets" / "js" / "ds_defensibility_data.js"
check(DS.is_file(), "ds_defensibility_data.js present")
if DS.is_file():
    ds = norm(DS.read_text(encoding="utf-8"))
    for phrase in ("the framework", "this framework", "our framework", "a new framework",
                   "framework refinement", "the associated framework"):
        check(phrase.lower() not in ds.lower(),
              f"no string claims a framework of its own ({phrase})", phrase)
    check("not a new governance framework" in ds,
          "and the lead still says the contribution is not a new governance framework")
    # The retired names, in the file the authority names as written around that framing.
    for retired in ("PCEIF", "PDAF"):
        check(retired not in ds, f"{retired} does not appear", retired)

print("\n17. The Methods and Framework tab label is spelled one way")
# NAMING_AUTHORITY.md: "User-facing text uses 'and', not the ampersand the code constants use."
# The tab button in index.html said "and" while the fly-out pill in app.js said "&": the same
# label, two spellings, one of them against the authority.
#
# THE WORD "FRAMEWORK" IN THIS LABEL IS NOT DECIDED HERE. Whether the tab should be renamed is a
# judgement the authority does not settle, and the report puts it to Lin rather than this file
# asserting an answer. What is checked is only the spelling rule, which the authority does settle.
LABEL_FILES = (LIVE, ROOT / "assets" / "js" / "app.js", ROOT / "assets" / "js" / "knowledge.js")
for path in LABEL_FILES:
    check(path.is_file(), f"{path.name} present")
    if path.is_file():
        body = path.read_text(encoding="utf-8")
        check("Methods & Framework" not in body,
              f"{path.name} does not use the ampersand spelling")

print()
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
