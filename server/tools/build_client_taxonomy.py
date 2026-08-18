"""
RUN 32 FINAL CLOSURE. THE ONE GENERATOR FOR BOTH CLIENT TAXONOMY ARTIFACTS.

WHY THIS EXISTS. `assets/js/categories.js` and `assets/js/taxonomy.js` each carried a
hand-maintained copy of the same 101-module taxonomy. Two hand-maintained current authorities is
not a tidiness problem, it is a correctness one, and this repository has now paid for it twice:

  * the B3/B4.7 identifier drift was fixed FIRST in categories.js, which `index.html` does not
    load, so every source check passed while the live page stayed broken;
  * the two files had already silently diverged on their own -- nine modules carried
    `disabled: true` in taxonomy.js and not in categories.js.

THE FIELDS EACH AUTHORITY OWNS, and nothing owns a field twice:

    registry (server/app/simulation/registry.py + the registry map)
        name           the module's current authoritative name
        method_class   the identifier the production runner actually emits
        disabled       whether the registry disables it

    taxonomy_authority.json (this directory)
        everything the registry does not govern: category identity, colour and description, and
        each module's id, num, required inputs, sector applicability and level flags.

NEITHER GENERATED FILE IS HAND-MAINTAINED. Editing one of them cannot fix or break production,
because the guard regenerates from the authorities and compares; the only way to change what ships
is to change an authority and regenerate.

    python build_client_taxonomy.py            # writes both files
    python build_client_taxonomy.py --check    # exits 1 if either file is not what this produces
"""
from __future__ import annotations

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "server"))

from app.simulation import registry as REG                                  # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED as PV              # noqa: E402

AUTHORITY = HERE / "taxonomy_authority.json"
TARGETS = {
    "assets/js/categories.js": "categories.js",
    "assets/js/taxonomy.js": "taxonomy.js",
}
START = "window.LIN_CATEGORIES = ["


def js(value) -> str:
    """A JS literal in the house style: single-quoted strings, compact arrays."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, str):
        return "'" + value.replace("\\", "\\\\").replace("'", "\\'") + "'"
    if isinstance(value, list):
        return "[" + ",".join(js(v) for v in value) + "]"
    raise TypeError(type(value))


def build() -> str:
    authority = json.loads(AUTHORITY.read_text(encoding="utf-8"))
    names = {m["new_id"]: m["module_name"] for m in REG.load_registry()}
    lines = [
        "/* GENERATED BLOCK. Do not edit by hand.",
        "",
        "   Written by server/tools/build_client_taxonomy.py from TWO authorities, and neither",
        "   this file nor its sibling is hand-maintained. Editing the array below cannot change",
        "   what ships: the guard regenerates from the authorities and compares, so a hand edit",
        "   is reverted or caught. Change an authority and regenerate.",
        "",
        "     name, method_class, disabled   server/app/simulation/registry.py (and the",
        "                                    portfolio dispatch table) -- the identifiers the",
        "                                    production runners actually emit",
        "     everything else                server/tools/taxonomy_authority.json -- category",
        "                                    identity, colour, description, and each module's",
        "                                    id, num, required inputs, sectors and level flags",
        "",
        "   WHY. categories.js and taxonomy.js each carried a hand-maintained copy of the same",
        "   101-module taxonomy. index.html loads taxonomy.js and not categories.js, so a fix",
        "   made in the wrong copy passed every source check while the live page stayed broken;",
        "   and the two had already drifted apart on their own, with nine modules carrying",
        "   `disabled: true` in one and not the other. */",
        START,
    ]
    for ci, cat in enumerate(authority):
        lines.append("  {")
        lines.append("    id: %s, num: %s, name: %s," % (js(cat["id"]), js(cat["num"]),
                                                         js(cat["name"])))
        lines.append("    group: %s, groupName: %s," % (js(cat["group"]), js(cat["groupName"])))
        lines.append("    color: %s," % js(cat["color"]))
        lines.append("    description: %s," % js(cat["description"]))
        if "level" in cat:
            lines.append("    level: %s," % js(cat["level"]))
        lines.append("    modules: [")
        mods = cat["modules"]
        for mi, m in enumerate(mods):
            mid = m["num"]
            if mid not in names:
                raise SystemExit(f"{mid} is in the taxonomy authority and not in the registry")
            parts = ["id: %s" % js(m["id"]), "num: %s" % js(mid),
                     "name: %s" % js(names[mid])]
            # THE IDENTIFIER THE RUNNER ACTUALLY EMITS. A module with no dispatch entry keeps the
            # authority's own value, which is the case for the supplied and portfolio identities.
            if mid in REG.VALIDATED:
                parts.append("method_class: %s" % js(REG.VALIDATED[mid][0]))
            elif mid in PV:
                parts.append("method_class: %s" % js(PV[mid]))
            elif "method_class" in m:
                # An identity the platform neither dispatches nor computes -- the supplied
                # Document Risk Score. No server authority governs its class, so the taxonomy
                # authority carries it.
                parts.append("method_class: %s" % js(m["method_class"]))
            for k in ("active", "authoringOnly", "excludeFromProjectStatus", "portfolioLevel"):
                if k in m:
                    parts.append("%s: %s" % (k, js(m[k])))
            if mid in REG.DISABLED_MODULES:
                parts.append("disabled: true")
            for k in ("required", "sectors"):
                if k in m:
                    parts.append("%s: %s" % (k, js(m[k])))
            lines.append("      { " + ", ".join(parts) + " }"
                         + ("," if mi < len(mods) - 1 else ""))
        lines.append("    ]")
        lines.append("  }" + ("," if ci < len(authority) - 1 else ""))
    lines.append("];")
    return "\n".join(lines) + "\n"


BANNER = "/* GENERATED BLOCK. Do not edit by hand."


def splice(path: pathlib.Path, block: str) -> str:
    src = path.read_text(encoding="utf-8")
    # Replace from the BANNER when one is already present, not from the array: anchoring on the
    # array alone would leave the previous banner in place and stack a new one on every run.
    i = src.index(BANNER) if BANNER in src else src.index(START)
    # The array ends at the first line that is exactly "];" at column 0.
    j = src.index("\n];", i) + len("\n];\n")
    return src[:i] + block + src[j:]


def main() -> int:
    block = build()
    bad = []
    for rel in TARGETS:
        p = ROOT / rel
        want = splice(p, block)
        if "--check" in sys.argv:
            if p.read_text(encoding="utf-8") != want:
                bad.append(rel)
        else:
            p.write_text(want, encoding="utf-8")
            print(f"wrote {rel}")
    if bad:
        print("NOT GENERATED FROM THE CURRENT AUTHORITIES:", bad)
        return 1
    if "--check" in sys.argv:
        print("both client artifacts are exactly what the authorities generate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
