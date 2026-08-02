"""
The live disclaimer text must equal its reviewable source, character for character.

WHY THIS EXISTS. The liability notices are approved wording. The approval is recorded in
DISCLAIMERS_DRAFT.md, and the text a user actually sees lives in index.html. Two copies of
approved legal text in two files is exactly the shape that drifts: someone tightens a sentence on
the live surface, the reviewed source still says the old thing, and nobody can say afterwards
which wording was approved. This check makes that divergence a red suite rather than a discovery.

WHAT IT DOES NOT DO. It does not judge the wording, and it cannot: a session may not extend or
strengthen liability language on its own judgement. It only asserts that what ships is what was
approved, and that both account types carry their own variant on both surfaces.

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
    for key, heading in (("research", "## 1."), ("operational", "## 2.")):
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

print()
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
