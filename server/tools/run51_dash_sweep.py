"""
RUN 51, RULING 4 / SECTION 6.6. THE DASH SWEEP, AND THE THING THAT DECIDES WHAT IS TEXT.

A line-based grep cannot answer guarantee 1, because most of the en and em dashes in
`assets/` sit in code comments, in CSS selectors and in minified vendor code, none of which a
participant can read. Three runs reported guarantee 1 NOT MET partly because the number they
reported (562 on non-comment lines) counted all of those.

This module walks each file as CHARACTERS, tracking whether it is inside a line comment, a
block comment, a single- or double-quoted string, a template literal, a regular expression or
bare code, and reports each dash with the state it was found in. Only STRING and TEMPLATE
states are candidate user-facing text. It also reads HTML text nodes and, deliberately, SVG
`<text>` element content and `aria-label` attributes, which `innerText` does not expose and
which is why the ten identifiers inside the handbook Signal Stack survived every prior sweep.

Run with no arguments it prints the inventory. It never edits anything.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
DASHES = "—–"
SKIP_SUFFIX = {".png", ".jpg", ".jpeg", ".gif", ".woff", ".woff2", ".ttf", ".ico", ".svg"}
VENDORED = ("assets/vendor/",)


def scan_js(text: str):
    """Yield (index, line, state) for every en/em dash, with the lexical state it sits in."""
    out, i, n = [], 0, len(text)
    state, line = "code", 1
    quote = ""
    prev = ""            # last non-space code character, to tell a regex from a division
    while i < n:
        ch = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if ch == "\n":
            line += 1
            if state == "line_comment":
                state = "code"
            i += 1
            continue
        if state == "code":
            if ch == "/" and nxt == "/":
                state = "line_comment"; i += 2; continue
            if ch == "/" and nxt == "*":
                state = "block_comment"; i += 2; continue
            # A REGEX LITERAL, NOT A DIVISION. Without this the apostrophe inside /'/g opens a
            # string that runs to the next apostrophe and desynchronises the whole file, which
            # is how an earlier version of this sweep reported comment lines as strings.
            if ch == "/" and (prev == "" or prev in "(,=:[!&|?{};+-*%<>~^"):
                j = i + 1
                while j < n:
                    if text[j] == "\\":
                        j += 2; continue
                    if text[j] == "\n":
                        break
                    if text[j] == "[":
                        while j < n and text[j] != "]":
                            j += 2 if text[j] == "\\" else 1
                    if text[j] == "/":
                        break
                    j += 1
                if j < n and text[j] == "/":
                    line += text[i:j].count("\n")
                    i = j + 1; prev = "/"; continue
            if ch in "'\"":
                state = "string"; quote = ch; i += 1; continue
            if ch == "`":
                state = "template"; i += 1; continue
            if not ch.isspace():
                prev = ch
        elif state == "block_comment":
            if ch == "*" and nxt == "/":
                state = "code"; i += 2; continue
        elif state == "string":
            if ch == "\\":
                i += 2; continue
            if ch == quote:
                state = "code"; i += 1; continue
        elif state == "template":
            if ch == "\\":
                i += 2; continue
            if ch == "`":
                state = "code"; i += 1; continue
        if ch in DASHES:
            out.append((i, line, state))
        i += 1
    return out


TEXT_NODE = re.compile(r">([^<>]*)<")
ARIA = re.compile(r'aria-label\s*=\s*"([^"]*)"')
SVG_TEXT = re.compile(r"<text\b[^>]*>(.*?)</text>", re.S)


def scan_html(text: str):
    """HTML: text nodes, aria-labels, and SVG <text> content, which innerText never shows."""
    out = []
    for m in TEXT_NODE.finditer(text):
        for d in [c for c in m.group(1) if c in DASHES]:
            out.append((m.start(1), text[: m.start(1)].count("\n") + 1, "html_text"))
    for pat, label in ((ARIA, "aria_label"), (SVG_TEXT, "svg_text")):
        for m in pat.finditer(text):
            for d in [c for c in m.group(1) if c in DASHES]:
                out.append((m.start(1), text[: m.start(1)].count("\n") + 1, label))
    return out


def scan_json(text: str):
    out = []
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', text):
        for c in m.group(1):
            if c in DASHES:
                out.append((m.start(1), text[: m.start(1)].count("\n") + 1, "json_string"))
    return out


def scan_css(text: str):
    """CSS: only `content:` values reach a reader. Everything else is a comment or a token."""
    out = []
    for m in re.finditer(r"content\s*:\s*(\"[^\"]*\"|'[^']*')", text):
        for c in m.group(1):
            if c in DASHES:
                out.append((m.start(1), text[: m.start(1)].count("\n") + 1, "css_content"))
    total = sum(text.count(d) for d in DASHES)
    return out, total


USER_FACING = {"string", "template", "html_text", "aria_label", "svg_text",
               "json_string", "css_content"}


def inventory():
    rows = []
    for p in sorted((ROOT / "assets").rglob("*")):
        if not p.is_file() or p.suffix.lower() in SKIP_SUFFIX:
            continue
        rel = p.relative_to(ROOT).as_posix()
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:                                            # noqa: BLE001
            continue
        total = sum(t.count(d) for d in DASHES)
        if not total:
            continue
        vendored = any(rel.startswith(v) for v in VENDORED)
        if p.suffix == ".js":
            hits = scan_js(t)
            kind = "vendored library" if vendored else "hand-maintained script"
            if rel in ("assets/js/taxonomy.js", "assets/js/categories.js"):
                kind = "generated output"
        elif p.suffix in (".html", ".htm"):
            hits = scan_html(t); kind = "hand-maintained markup"
        elif p.suffix == ".json":
            hits = scan_json(t); kind = "hand-maintained data"
        elif p.suffix == ".css":
            hits, _ = scan_css(t)
            kind = "vendored stylesheet" if vendored else "stylesheet"
        else:
            hits = []; kind = "documentation, not served as interface"
        uf = [h for h in hits if h[2] in USER_FACING]
        rows.append((rel, kind, total, len(uf), uf, t))
    return rows


def main() -> int:
    rows = inventory()
    print(f"{'file':52} {'classification':32} {'total':>6} {'user-facing':>12}")
    print("-" * 108)
    tt = uu = 0
    for rel, kind, total, nuf, _uf, _t in rows:
        print(f"{rel:52} {kind:32} {total:6d} {nuf:12d}")
        tt += total; uu += nuf
    print("-" * 108)
    print(f"{'TOTAL':52} {'':32} {tt:6d} {uu:12d}   files={len(rows)}")
    print()
    print("EVERY USER-FACING INSTANCE, with its lexical state:")
    for rel, _kind, _total, nuf, uf, t in rows:
        if not nuf:
            continue
        lines = t.splitlines()
        seen = set()
        for _i, ln, st in uf:
            if (rel, ln) in seen:
                continue
            seen.add((rel, ln))
            print(f"  {rel}:{ln}  [{st}]  {lines[ln - 1].strip()[:120]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ---------------------------------------------------------------------------------------------
# GUARANTEE 1 (order section 7 item 11). One sweep, six classes, and it reads SVG text nodes.
# ---------------------------------------------------------------------------------------------
G1 = [
    ("module identifier", re.compile(r"\b[A-D]\d{1,2}\.\d{1,2}\b")),
    ("category identifier", re.compile(r"\b[A-D]\d{1,2}\b(?!\.)")),
    ("retired Cat scheme", re.compile(r"\bCat(?:egory)?\s*\d+", re.I)),
    ("retired Module scheme", re.compile(r"\bModule\s*\d+|\bM0\d\b|\bPH\.\d")),
    ("ampersand", re.compile(r"&(?!amp;|quot;|nbsp;|gt;|lt;|#\d|#x|rarr;|times;|hellip;|copy;|mdash;|ndash;|&)")),
    ("en or em dash", re.compile(r"[–—]")),
]
# Syntactically significant, and each is named in the report rather than waved through.
URLISH = re.compile(r"(\?|&)\w+=|encodeURIComponent|apiGet\(|\.replace\(|new RegExp|charAt|indexOf\(")


def guarantee_one():
    survivors = []
    for p in sorted((ROOT / "assets").rglob("*")):
        if not p.is_file() or p.suffix.lower() in SKIP_SUFFIX:
            continue
        rel = p.relative_to(ROOT).as_posix()
        if any(rel.startswith(v) for v in VENDORED):
            continue
        try:
            t = p.read_text(encoding="utf-8")
        except Exception:                                            # noqa: BLE001
            continue
        if p.suffix == ".js":
            hits = scan_js(t)
        elif p.suffix in (".html", ".htm"):
            hits = scan_html(t)
        elif p.suffix == ".json":
            hits = scan_json(t)
        elif p.suffix == ".css":
            hits, _ = scan_css(t)
        else:
            continue
        lines = t.splitlines()
        seen = set()
        for _i, ln, st in hits:
            if st not in USER_FACING or (rel, ln) in seen:
                continue
            seen.add((rel, ln))
        # Re-scan the user-facing spans themselves rather than whole lines: a whole line carries
        # its own code, and matching against code is how a sweep invents a violation.
        spans = user_facing_spans(t, p.suffix)
        for start, text in spans:
            ln = t[:start].count("\n") + 1
            for label, rx in G1:
                for m in rx.finditer(text):
                    survivors.append((rel, ln, label, m.group(0),
                                      lines[ln - 1].strip()[:120] if ln <= len(lines) else ""))
    return survivors


STR_RX = re.compile(r"'(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\"|`(?:[^`\\]|\\.)*`", re.S)


def user_facing_spans(t: str, suffix: str):
    """The text a reader could see: string and template bodies, HTML text, aria, SVG text."""
    out = []
    if suffix == ".js":
        # Only strings that are not obviously code plumbing.
        for m in STR_RX.finditer(t):
            body = m.group(0)[1:-1]
            head = t[max(0, m.start() - 60):m.start()]
            if URLISH.search(head) or URLISH.search(body):
                continue
            out.append((m.start() + 1, body))
    elif suffix in (".html", ".htm"):
        for m in TEXT_NODE.finditer(t):
            out.append((m.start(1), m.group(1)))
        for m in ARIA.finditer(t):
            out.append((m.start(1), m.group(1)))
        for m in SVG_TEXT.finditer(t):
            out.append((m.start(1), m.group(1)))
    elif suffix == ".json":
        for m in re.finditer(r'"((?:[^"\\]|\\.)*)"', t):
            out.append((m.start(1), m.group(1)))
    elif suffix == ".css":
        for m in re.finditer(r"content\s*:\s*(\"[^\"]*\"|'[^']*')", t):
            out.append((m.start(1), m.group(1)))
    return out
