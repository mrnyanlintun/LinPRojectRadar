"""
RUN 32 FINAL CLOSURE. THE PER-MODULE HANDBOOK SURFACE EXISTS AND RESOLVES.

TWO CLOSURES RECORDED THIS SURFACE NOT_VERIFIED, and both times the cause was navigation rather
than absence. It is real: Handbook -> the "Methods and Framework" tab -> a per-category "module
reference" topic, registered in MODREF_TOPICS and resolved by lookupTopic(), which renders every
module's documentation through modDoc() -- including the "Status. Proxy: ..." line the qualifier
map drives. Classification: CURRENT_REQUIRED_SURFACE.

This guard checks the surface is WIRED. The authenticated browser run
(run32_qualifier_browser_verification.py) checks that it RENDERS, and reached 101 module sections.
Both are needed: a wired topic that never renders and a rendering that no route reaches are
different failures.
"""
from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "server"))

from app.simulation import registry as REG                                  # noqa: E402

PASSED = FAILED = 0
_fail: list[str] = []


def check(ok, label, detail=""):
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        _fail.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


KN = (ROOT / "assets/js/knowledge.js").read_text(encoding="utf-8")

#: The per-category module-reference topics this surface is required to register. Declared here
#: so that a topic which stops existing is a RED check rather than a silently shorter list.
MODREF_PREFIXES = (
    "cat1-modules", "cat2-modules", "cat3-modules", "cat4-modules", "cat5-modules",
    "cat6-modules", "cat7-modules", "cat9-modules", "cat10-modules", "cat11-modules",
    "ph-modules",
)

print("=== 1. THE SURFACE IS REGISTERED AND ROUTED ===")

check("const MODREF_TOPICS = {" in KN,
      "the per-module reference topics are registered in MODREF_TOPICS")
check("if (MODREF_TOPICS[id]) return MODREF_TOPICS[id];" in KN,
      "the per-module handbook surface resolves its module-reference topics: lookupTopic() "
      "returns a MODREF topic, which is the route two earlier closures failed to reach")
check("function modDoc(" in KN and "mods.map(modDoc)" in KN,
      "and a resolved topic renders every module through modDoc()")

block = KN[KN.index("const MODREF_TOPICS = {"):]
block = block[:block.index("\n  };")]
declared = set(re.findall(r'"([\w-]+)":\s*\{', block))
missing = sorted(t for t in MODREF_PREFIXES if t not in declared)
check(not missing,
      "every declared module-reference topic exists in the handbook, so a surface cannot be "
      "claimed as verified when it is not registered", str(missing))

print("\n=== 2. THE SURFACE COVERS THE WHOLE REGISTRY ===")

# Each topic builds from a CAT*_MODULES / PH_MODULES array. Every registry identity must appear
# in exactly one of those arrays, or a module has documentation nowhere.
entries = re.findall(r'\{ n: "([A-D]\d+\.\d+)", name: "([^"]*)", mc: "([^"]*)"', KN)
documented = {n for n, _nm, _mc in entries}
reg = {m["new_id"]: m["module_name"] for m in REG.load_registry()}
check(set(reg) - documented == set(),
      f"every one of the registry's {len(reg)} identities has a handbook entry, derived from the "
      f"registry rather than counted here", str(sorted(set(reg) - documented)[:8]))
check(documented - set(reg) == set(),
      "and the handbook documents no module the registry does not declare",
      str(sorted(documented - set(reg))[:8]))
dupes = sorted({n for n in documented if [x for x, _, _ in entries].count(n) > 1})
check(not dupes, "no module is documented twice", str(dupes))

print("\n=== 3. WHAT THE SURFACE SAYS AGREES WITH THE AUTHORITIES ===")

bad_name = sorted(f"{n}: {nm!r} vs {reg[n]!r}" for n, nm, _mc in entries
                  if n in reg and nm != reg[n])
check(not bad_name, "every documented name is the registry's current name", "; ".join(bad_name[:4]))
bad_mc = sorted(f"{n}: {mc!r} vs {REG.VALIDATED[n][0]!r}" for n, _nm, mc in entries
                if n in REG.VALIDATED and mc != REG.VALIDATED[n][0])
check(not bad_mc, "every documented method class is the identifier its runner emits",
      "; ".join(bad_mc[:4]))

print()
for f in _fail:
    print("FAIL:", f)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
