#!/usr/bin/env python3
"""Attach the v19 governed assessment to the analytical suites that need it."""
import pathlib, re, sys
TOOLS = pathlib.Path(__file__).resolve().parent
BLOCK = '''
# =================================================================================================
# RUN 31 v19: THIS SUITE SUPPLIES THE GOVERNED CATEGORY-9 ASSESSMENT ITS MODULES NOW REQUIRE.
#
# From sim-2026.08-v19 a package with no Category-9 assessment FAILS CLOSED for every
# Category-6/7/8/10 consumer. This suite's purpose is a module's ARITHMETIC, so it supplies the
# ordinary governed assessment a real caller supplies, through the ordinary signal-input key, and
# then tests the arithmetic it was written to test. It is not exempt from the gate: the ordinary
# precedence still applies, and the gate's own guards never install this.
# =================================================================================================
import run31_qualified_fixture as _R31Q                                       # noqa: E402
_R31Q.install()

'''
NAMES = sys.argv[1:]
for name in NAMES:
    p = TOOLS / name
    if not p.is_file():
        print(f"  !! missing {name}"); continue
    s = p.read_text()
    if "_R31Q" in s:
        print(f"  already applied: {name}"); continue
    lines = s.splitlines(keepends=True)
    depth = 0; last = 0
    for i, l in enumerate(lines[:300]):
        depth += l.count("(") - l.count(")")
        if re.match(r'^(from|import)\s', l) and depth == 0:
            last = i
    lines.insert(last + 1, BLOCK)
    p.write_text("".join(lines))
    print(f"  applied: {name}")
