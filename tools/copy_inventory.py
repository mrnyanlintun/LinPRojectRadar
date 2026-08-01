"""Inventory user-facing copy: em dashes and spelling, strings only, comments excluded."""
import io, re, glob, os, sys

EM = "—"

SQ = r"'(?:[^'\\\n]|\\.)*'"
DQ = r'"(?:[^"\\\n]|\\.)*"'
BQ = r"`(?:[^`\\]|\\.)*`"
STR_JS = re.compile(SQ + "|" + DQ + "|" + BQ)
STR_PY = re.compile(SQ + "|" + DQ)


def js_strings(t):
    t = re.sub(r"/\*.*?\*/", "", t, flags=re.S)
    t = re.sub(r"^\s*//.*$", "", t, flags=re.M)
    return [m.group(0) for m in STR_JS.finditer(t)]


def py_strings(t):
    t = re.sub(r'"""(?:.|\n)*?"""', "", t)      # docstrings are not user-facing
    t = re.sub(r"^\s*#.*$", "", t, flags=re.M)
    return [m.group(0) for m in STR_PY.finditer(t)]


def html_parts(t):
    """(markup text, inline script source) with comments and styles removed."""
    scripts = "\n".join(re.findall(r"<script[^>]*>(.*?)</script>", t, flags=re.S))
    m = re.sub(r"<!--.*?-->", "", t, flags=re.S)
    m = re.sub(r"<style.*?</style>", "", m, flags=re.S)
    m = re.sub(r"<script.*?</script>", "", m, flags=re.S)
    return m, scripts


HTML = [f for f in ["index.html", "tests.html", "research/deepdive.html"] if os.path.exists(f)]
JS = sorted(f.replace("\\", "/") for f in glob.glob("assets/js/*.js"))
PY = sorted(f.replace("\\", "/") for f in glob.glob("server/app/*.py"))

rows = []
for f in HTML:
    t = io.open(f, encoding="utf-8", errors="replace").read()
    markup, scripts = html_parts(t)
    n = markup.count(EM) + sum(s.count(EM) for s in js_strings(scripts))
    if n:
        rows.append((f, n))
for f in JS:
    n = sum(s.count(EM) for s in js_strings(io.open(f, encoding="utf-8", errors="replace").read()))
    if n:
        rows.append((f, n))
for f in PY:
    n = sum(s.count(EM) for s in py_strings(io.open(f, encoding="utf-8", errors="replace").read()))
    if n:
        rows.append((f, n))

print("EM DASHES IN USER-FACING COPY (comments and docstrings excluded): %d" % sum(n for _, n in rows))
print()
for f, n in sorted(rows, key=lambda r: -r[1]):
    print("   %4d  %s" % (n, f))

# Spelling, in user-facing strings only.
PAIRS = [("authorised", "authorized"), ("authorisation", "authorization"),
         ("organisation", "organization"), ("recognised", "recognized"),
         ("summarised", "summarized"), ("behaviour", "behavior"),
         ("licence", "license"), ("centre", "center"),
         ("analyse", "analyze"), ("catalogue", "catalog"),
         ("prioritise", "prioritize"), ("utilise", "utilize")]

tally = {p: [0, 0] for p in PAIRS}
for f in HTML:
    t = io.open(f, encoding="utf-8", errors="replace").read()
    markup, scripts = html_parts(t)
    blob = (markup + " " + " ".join(js_strings(scripts))).lower()
    for p in PAIRS:
        tally[p][0] += blob.count(p[0]); tally[p][1] += blob.count(p[1])
for f in JS:
    blob = " ".join(js_strings(io.open(f, encoding="utf-8", errors="replace").read())).lower()
    for p in PAIRS:
        tally[p][0] += blob.count(p[0]); tally[p][1] += blob.count(p[1])
for f in PY:
    blob = " ".join(py_strings(io.open(f, encoding="utf-8", errors="replace").read())).lower()
    for p in PAIRS:
        tally[p][0] += blob.count(p[0]); tally[p][1] += blob.count(p[1])

print()
print("SPELLING IN USER-FACING COPY   british | american")
brit = amer = 0
for (b, a), (cb, ca) in tally.items():
    if cb or ca:
        print("   %-16s %4d | %-16s %4d" % (b, cb, a, ca))
        brit += cb; amer += ca
print("   %-16s %4d | %-16s %4d" % ("TOTAL", brit, "TOTAL", amer))
