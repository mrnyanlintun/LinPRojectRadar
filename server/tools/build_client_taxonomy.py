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
        each module's id, module_id, required inputs, sector applicability and level flags.

NEITHER GENERATED FILE IS HAND-MAINTAINED. Editing one of them cannot fix or break production,
because the guard regenerates from the authorities and compares; the only way to change what ships
is to change an authority and regenerate.

    python build_client_taxonomy.py            # writes both files
    python build_client_taxonomy.py --check    # exits 1 if either file is not what this produces

RUN 52, RULING 3. ONE NAME FOR THE MODULE IDENTIFIER ON BOTH SIDES OF THE WIRE: `module_id`.
Run 51 moved this field from `num` to `key`; the server already called the same thing
`module_id` in the registry, the qualifier closure and the acceptance builders. Two names for
one thing is what produced the original identifier defect, so the client and the authority move
to the server's name rather than the server moving to theirs.

WHAT DID NOT MOVE, AND WHY. The CATEGORY identifier -- "A1", "B4" -- keeps the field name `key`.
A category is not a module: `module_id` on a category object would be a third wrong name, not a
consistent one. Ruling 3 names the MODULE identifier and only that field moved.
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
    # THE POPULATION IS THE ONE IN SERVICE, NOT THE WHOLE REGISTRY. registry_index() /
    # load_registry() resolve retired identifiers by design (registry.py:426); service_index()
    # (registry.py:440) is the population in service, derived from the retirement notes in
    # p0-baseline/module_renumbering_map.csv and from nothing else. The client taxonomy is a
    # participant surface, so a retired identity must not reach it. Reinstating a module in the
    # CSV puts it back here with no edit to this generator.
    names = {mid: row["module_name"] for mid, row in REG.service_index().items()}
    # RUN 51, SECTION 6.1. THE COUNTS SHIP DERIVED, NOT TYPED. Every user-facing statement of
    # how many modules the platform registers, how many are in service, how many were retired
    # and how many the analytical server computes was a hand-typed number in prose, which is
    # what produced the "96 registered modules" the owner saw on the handbook. They are counted
    # here from the SAME authorities the array is built from -- registry_index() for what is
    # registered, service_index() for what is in service, VALIDATED for what has a production
    # runner -- and the surfaces read them. A retirement changes every sentence with no edit.
    _registered = len(REG.registry_index())
    _in_service = len(REG.service_index())
    _computes = len([m for m in REG.service_index() if m in REG.VALIDATED])
    counts = ("window.LIN_TAXONOMY_COUNTS = { registered: %d, inService: %d, retired: %d, "
              "serverComputes: %d, supplied: %d };"
              % (_registered, _in_service, _registered - _in_service,
                 _computes, _in_service - _computes))
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
        "                                    id, module_id, required inputs, sectors and level flags",
        "",
        "   WHY. categories.js and taxonomy.js each carried a hand-maintained copy of the same",
        "   101-module taxonomy. index.html loads taxonomy.js and not categories.js, so a fix",
        "   made in the wrong copy passed every source check while the live page stayed broken;",
        "   and the two had already drifted apart on their own, with nine modules carrying",
        "   `disabled: true` in one and not the other. */",
        counts,
        START,
    ]
    # RUN 95. A CATEGORY THAT HOLDS NO MODULE IN SERVICE IS NOT EMITTED AT ALL.
    #
    # The owner's ruling, Run 95 section 3: "An empty category is not a category that failed to
    # report -- there is nothing in it to report." Before this run the generator emitted every
    # category the authority declares whatever its module list came to, so a category all of
    # whose modules had been retired would have shipped as a named, coloured entry with an empty
    # `modules: []` -- drawn on both charts, counted among the performance categories, and
    # saying nothing. That is exactly what "nothing that carries no meaning may look as though it
    # does" forbids.
    #
    # DERIVED, NOT LISTED. There is no category name written here. A category is emitted if and
    # only if at least one of its authority modules is in `service_index()`. Retiring the last
    # module of a category removes the category, and reinstating one in the registry CSV brings
    # it back, with no edit to this generator and none to either client artifact. This is the
    # SAME rule as the module filter twelve lines below, one level up.
    #
    # SCOPED TO GROUP A, AND THE SCOPE IS A CORRECTION MADE INSIDE RUN 95 AFTER MEASURING.
    # The first form of this filter applied to EVERY category and removed TWO, not one: it also
    # removed D1 Portfolio Health, whose five modules were all retired at RUN 43 and which has
    # shipped as a declared, empty, portfolio-level category ever since without anyone treating
    # that as a defect. `test_map_and_module_count.py` depends on its presence -- it checks that
    # "the taxonomy genuinely has a portfolio-level category to exclude", which is what stops the
    # project-level filters below it from being vacuous -- so removing it would have made a real
    # check assert nothing. The tree's own precedent for an empty PORTFOLIO-LEVEL category is
    # that it stays, and this run does not overturn a precedent it was not asked to touch.
    #
    # The owner's ruling is about the performance categories the two charts and the project
    # status draw, and those are exactly the GROUP A project-level ones. `group` is a field on
    # the authority row, so the scope is derived here too: still no category name is written.
    #
    # So exactly ONE category is removed, and that is measured rather than assumed: A5 System
    # Dynamics & Complexity, which lost its last five modules in service at Run 95. Every other
    # group A category still holds at least one.
    authority = [c for c in authority
                 if c["group"] != "A"
                 or any(m["module_id"] in names for m in c["modules"])]
    for ci, cat in enumerate(authority):
        lines.append("  {")
        lines.append("    id: %s, key: %s, name: %s," % (js(cat["id"]), js(cat["key"]),
                                                         js(cat["name"])))
        lines.append("    group: %s, groupName: %s," % (js(cat["group"]), js(cat["groupName"])))
        lines.append("    color: %s," % js(cat["color"]))
        lines.append("    description: %s," % js(cat["description"]))
        if "level" in cat:
            lines.append("    level: %s," % js(cat["level"]))
        lines.append("    modules: [")
        for _m in cat["modules"]:
            if _m["module_id"] not in names and not REG.is_retired(_m["module_id"]):
                raise SystemExit(
                    f"{_m['module_id']} is in the taxonomy authority and not in the registry")
        # Retired identities are dropped from the emitted array. The comma/terminator logic below
        # counts the emitted rows, so the filter happens here rather than inside the loop.
        mods = [_m for _m in cat["modules"] if _m["module_id"] in names]
        for mi, m in enumerate(mods):
            mid = m["module_id"]
            parts = ["id: %s" % js(m["id"]), "module_id: %s" % js(mid),
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
