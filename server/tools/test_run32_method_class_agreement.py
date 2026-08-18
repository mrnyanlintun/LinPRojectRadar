"""
RUN 32 FINAL CLOSURE. THE CLIENT'S METHOD-CLASS IDENTIFIERS, CHECKED AGAINST THE RUNNERS.

WHY THIS GUARD DID NOT EXIST AND SHOULD HAVE. A method class is a JOIN KEY: the client resolves a
module's status by matching its own `method_class` against the one the server stamped on the
stored row. When a rename moves the server's identifier and the client's is left behind, THE JOIN
DOES NOT FAIL -- `Array.prototype.find` returns undefined, the lookup returns null, and the module
simply never appears. Six modules were in that state: A1.10 and A1.11 from Run 28's renames, and
B3.2 to B3.5 from Run 31's. Nothing anywhere went red for two and four runs respectively.

So this compares the CLIENT TAXONOMY against `registry.VALIDATED`, which is where the identifier
the runner actually emits lives. It reads no other copy of the mapping.

The population is derived from the taxonomy file itself. No module count is written down here.
"""

from __future__ import annotations

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(HERE))

from app.simulation import registry as REG                                  # noqa: E402
import participant_packages as PP                                           # noqa: E402

PASSED = 0
FAILED = 0
_fail: list[str] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        _fail.append(label)
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def taxonomy(rel: str) -> dict[str, tuple[str, str]]:
    s = (ROOT / rel).read_text(encoding="utf-8")
    return {m.group(1): (m.group(2), m.group(3)) for m in re.finditer(
        r"num: '([A-D]\d+\.\d+)', name: '([^']*)', method_class: '([^']*)'", s)}


print("=== 1. EVERY CLIENT METHOD CLASS IS THE ONE ITS RUNNER EMITS ===")

for rel in ("assets/js/categories.js", "assets/js/taxonomy.js"):
    tax = taxonomy(rel)
    check(bool(tax), f"{rel}: the taxonomy rows parse")
    drift = sorted(f"{mid}: client {mc!r} vs runner {REG.VALIDATED[mid][0]!r}"
                   for mid, (_n, mc) in tax.items()
                   if mid in REG.VALIDATED and mc != REG.VALIDATED[mid][0])
    check(not drift,
          f"{rel}: no module carries a method class its production runner has stopped emitting, "
          f"which is the join key a stale identifier silently breaks",
          "; ".join(drift[:6]))
    names = sorted(f"{mid}: client {nm!r}" for mid, (nm, _mc) in tax.items()
                   if mid in REG.VALIDATED
                   and nm != next((r["module_name"] for r in REG.load_registry()
                                   if r["new_id"] == mid), nm))
    check(not names, f"{rel}: and every displayed name is the registry's current name",
          "; ".join(names[:4]))

print("\n=== 2. THE HELP SURFACE USES THE SAME IDENTIFIERS ===")

_kn = (ROOT / "assets/js/knowledge.js").read_text(encoding="utf-8")
_kn_drift = sorted(f"{m.group(1)}: {m.group(3)!r} vs {REG.VALIDATED[m.group(1)][0]!r}"
                   for m in re.finditer(
                       r'\{ n: "([A-D]\d+\.\d+)", name: "([^"]*)", mc: "([^"]*)"', _kn)
                   if m.group(1) in REG.VALIDATED
                   and m.group(3) != REG.VALIDATED[m.group(1)][0])
check(not _kn_drift, "knowledge.js: every handbook entry's method class is the current one",
      "; ".join(_kn_drift[:6]))

print("\n=== 3. THE PROXY-QUALIFIER MIRROR IS KEYED ON CURRENT IDENTIFIERS ===")

# The mirror is keyed by method_class and states registry.PROXY_QUALIFIERS is its source of truth.
# A stale KEY means a qualifier the server still holds silently stops rendering, which is what had
# happened to B3.5's.
_blk = _kn[_kn.index("const RUN1_PROXY_QUALIFIER = {"):]
_blk = _blk[:_blk.index("\n  };")]
_client_keys = set(re.findall(r"^\s{4}(\w+):", _blk, re.M))
_server_classes = {REG.VALIDATED[k][0] for k in REG.PROXY_QUALIFIERS if k in REG.VALIDATED}
_missing = sorted(_server_classes - _client_keys)
check(not _missing,
      "every proxy qualifier the server still holds is reachable under the identifier the runner "
      "emits, so none of them silently stops rendering", str(_missing))
_superseded = sorted(k for k in _client_keys
                     if k in {v for v in PP.V9_METHOD_CLASS_PROPAGATION.values()})
check(not _superseded,
      "and no mirror key is a superseded identifier, which would be a stale key repaired into a "
      "stale claim rather than removed", str(_superseded))

print("\n=== 4. ALIASES EXIST FOR STORED ROWS AND ARE NEVER PRIMARY ===")

_cat = (ROOT / "assets/js/categories.js").read_text(encoding="utf-8")
check("window.LIN_HISTORICAL_METHOD_CLASS" in _cat,
      "the historical alias map is declared, so a row stored before a rename still joins")
check("window.linMethodClassMatches(m.method_class, cls)" in _cat,
      "and the status lookup matches through it rather than on equality alone, which is the "
      "comparison that returned null for six modules")
_tax_rows = taxonomy("assets/js/categories.js")
_alias_values = {v for v in PP.V9_METHOD_CLASS_PROPAGATION.values()}
_primary = sorted(mid for mid, (_n, mc) in _tax_rows.items() if mc in _alias_values)
check(not _primary,
      "NO superseded identifier is a current primary: an alias is matched against and never "
      "displayed, emitted or carried by a taxonomy row", str(_primary))
for _cur, _old in sorted(PP.V9_METHOD_CLASS_PROPAGATION.items()):
    check(re.search(r'\b%s:\s*\[\s*"%s"\s*\]' % (re.escape(_cur), re.escape(_old)), _cat)
          is not None,
          f"the alias map carries {_old} as history for {_cur}")

print("\n=== 4b. THE ALIAS MAP IS ON THE LIVE PARTICIPANT SURFACE, NOT ONLY THE SUPERSEDED ONE ===")

# index.html LOADS taxonomy.js AND NOT categories.js. An alias map declared only in
# categories.js is never loaded by the page a participant reads, so this asserts the live file
# carries it and that the two files agree. This run's first fix went into categories.js alone
# and the authenticated browser check is what caught it.
_tax_src = (ROOT / "assets/js/taxonomy.js").read_text(encoding="utf-8")
_index = (ROOT / "index.html").read_text(encoding="utf-8")
check("assets/js/taxonomy.js" in _index,
      "index.html loads taxonomy.js, which is therefore the live participant surface")
check("assets/js/categories.js" not in _index,
      "and does NOT load categories.js, so a fix made only there never reaches a participant")
check("window.LIN_HISTORICAL_METHOD_CLASS" in _tax_src,
      "taxonomy.js declares the historical alias map itself")
# The resolver itself must read METHOD_TO_NUM[methodClass] exactly ONCE -- that is its body. More
# than once means a call site bypasses it; zero means the resolver was rewritten into calling
# itself, which is exactly the recursion this closure had to fix.
_direct = _tax_src.count("METHOD_TO_NUM[methodClass]")
check("function numForMethodClass" in _tax_src and _direct == 1,
      "and every method-class to module-number lookup goes through the resolver, which reads the "
      "map exactly once: more would be a call site bypassing it, none would be the resolver "
      "calling itself", f"METHOD_TO_NUM[methodClass] appears {_direct} times")
for _cur, _old in sorted(PP.V9_METHOD_CLASS_PROPAGATION.items()):
    check(re.search(r'\b%s:\s*\[\s*"%s"\s*\]' % (re.escape(_cur), re.escape(_old)),
                    _tax_src) is not None,
          f"taxonomy.js carries {_old} as history for {_cur}")

print("\n=== 4c. THE LIVE FILE'S OWN CONSUMERS ARE EXECUTED, NOT READ ===")

# THIS SECTION EXISTS BECAUSE A STRING CHECK MISSED A SHIPPED CRASH. The previous closure
# rewrote the three method-class lookups in taxonomy.js to go through one resolver, and the
# blanket rewrite caught the RESOLVER'S OWN BODY as a fourth call site, so it called itself.
# Every status and result lookup on a project with a stored row threw
# "RangeError: Maximum call stack size exceeded" -- on the LIVE participant surface -- and the
# whole suite stayed green, because every guard on this file compared strings and the one
# execution probe drove the OTHER client file. So the live consumers are executed here.
import json as _j, shutil as _sh, subprocess as _sp, tempfile as _tf                # noqa: E402

_node2 = _sh.which("node")
if not _node2:
    check(False, "node is available to execute the live consumers",
          "node not found; the execution proof cannot run and is NOT marked passed")
else:
    _probe2 = """
const fs = require('fs');
global.window = global;
eval(fs.readFileSync(process.argv[2] + '/assets/js/taxonomy.js', 'utf8'));
const pairs = JSON.parse(process.argv[3]);
const project = { id: 'P', storedResult: {
  module_results: Object.keys(pairs).map(n => ({ module_id: n, method_class: pairs[n],
                                                 status_color: 'Amber' })),
  abstained: [] } };
const out = {};
for (const n of Object.keys(pairs)) {
  const mc = pairs[n];
  for (const fn of ['getModuleStatus', 'getModuleResult', 'getModuleAbstentionReason']) {
    try { const v = window[fn](mc, project);
          out[n + '|' + fn] = { ok: true, value: v === null ? null : (v.module_id || v) }; }
    catch (e) { out[n + '|' + fn] = { ok: false, error: e.constructor.name }; }
  }
}
console.log(JSON.stringify(out));
"""
    with _tf.NamedTemporaryFile("w", suffix=".js", delete=False) as _fh2:
        _fh2.write(_probe2)
        _pp = _fh2.name
    _pairs2 = {m: REG.VALIDATED[m][0] for m in sorted(REG.VALIDATED)}
    _r2 = _sp.run([_node2, _pp, str(ROOT), _j.dumps(_pairs2)],
                  capture_output=True, text=True, timeout=300)
    check(_r2.returncode == 0, "the live consumers execute without error",
          (_r2.stderr or "")[-240:])
    _res2 = _j.loads(_r2.stdout) if _r2.returncode == 0 and _r2.stdout.strip() else {}
    _threw = sorted(k for k, v in _res2.items() if not v.get("ok"))
    check(bool(_res2) and not _threw,
          "NO live consumer throws: getModuleStatus, getModuleResult and "
          "getModuleAbstentionReason all execute for every registered module against a stored row",
          str(_threw[:6]))
    _wrong = sorted(k for k, v in _res2.items()
                    if v.get("ok") and k.endswith("|getModuleResult")
                    and v.get("value") not in (None, k.split("|")[0]))
    check(bool(_res2) and not _wrong,
          "and every stored-row lookup returns THAT module's row, never another's",
          str(_wrong[:6]))
    _null = sorted(k for k, v in _res2.items()
                   if v.get("ok") and k.endswith("|getModuleStatus") and v.get("value") is None)
    check(bool(_res2) and not _null,
          "and no module's status resolves to a silent null against a row that contains it",
          str(_null[:6]))

print("\n=== 5. THE LOOKUP ACTUALLY RESOLVES, EXECUTED IN NODE AGAINST THE REAL CLIENT FILE ===")

# STRING CHECKS CANNOT SEE A SILENT EMPTY RESULT. Sections 1 to 4 prove the identifiers agree;
# they cannot prove the join works, and the whole defect was a join that returned null instead of
# failing. So the REAL `categories.js` is executed against a signal array shaped as the SERVER
# produces one, and every module is required to resolve to ITSELF -- not to null, and not to some
# other module.
import json as _json                                                        # noqa: E402
import shutil as _shutil                                                    # noqa: E402
import subprocess as _subprocess                                            # noqa: E402
import tempfile as _tempfile                                                # noqa: E402

_node = _shutil.which("node")
if not _node:
    check(False, "node is available to execute the client lookup",
          "node not found; the execution proof cannot be run and is NOT marked passed")
else:
    # The six renamed identities, derived from the taxonomy rather than listed here.
    _mods = sorted(m for m, (_n, mc) in _tax_rows.items()
                   if mc in PP.V9_METHOD_CLASS_PROPAGATION)
    _pairs = {m: mc for m, (_n, mc) in _tax_rows.items() if m in REG.VALIDATED}
    _arr = [{"method_class": REG.VALIDATED[m][0], "status_color": "Amber", "module_id": m}
            for m in _pairs]
    # The module/identifier pairs are passed IN as JSON rather than re-parsed inside the probe:
    # a regex nested through Python, a heredoc and a JS literal is exactly where an escaping bug
    # hides, and a probe that silently matches nothing would report the defect it is looking for.
    _probe = (
        "const fs = require('fs');\n"
        "global.window = global;\n"
        "const arr = JSON.parse(process.argv[3]);\n"
        "const pairs = JSON.parse(process.argv[4]);\n"
        "eval(fs.readFileSync(process.argv[2] + '/assets/js/categories.js', 'utf8'));\n"
        # A FULLY POPULATED project: `getModuleStatus` routes a handful of identities to
        # project.signals rather than to the signal array (the earned-value core, the anomaly
        # monitor, the document signal and the governance dominance state). Leaving those empty
        # would make them read as unresolved when they are simply served from elsewhere.
        "const project = { signals: { mc: { status: 'Amber' }, cusum: { status: 'Amber' },\n"
        "    doc: { status: 'Amber' }, decision: { state: 'Amber' } },\n"
        "  simulationSignals: { signal_array: arr } };\n"
        "const out = {};\n"
        "for (const num of Object.keys(pairs)) {\n"
        "  const mc = pairs[num];\n"
        "  const hit = arr.find(m => window.linMethodClassMatches(m.method_class, mc));\n"
        "  out[num] = { status: window.getModuleStatus(mc, project),\n"
        "               resolvedTo: hit ? hit.module_id : null };\n"
        "}\n"
        "console.log(JSON.stringify(out));\n")
    with _tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as _fh:
        _fh.write(_probe)
        _probe_path = _fh.name
    _r = _subprocess.run([_node, _probe_path, str(ROOT), _json.dumps(_arr), _json.dumps(_pairs)],
                         capture_output=True, text=True, timeout=180)
    check(_r.returncode == 0, "the client lookup executes without error",
          (_r.stderr or "")[-300:])
    _res = _json.loads(_r.stdout) if _r.returncode == 0 and _r.stdout.strip() else {}
    _empty = sorted(m for m in _mods if (_res.get(m) or {}).get("status") is None)
    check(bool(_res) and not _empty,
          "every renamed module's status RESOLVES rather than silently returning null, which is "
          "the failure the stale identifiers produced", str(_empty))
    _wrong = sorted(f"{m}->{(_res.get(m) or {}).get('resolvedTo')}" for m in _mods
                    if (_res.get(m) or {}).get("resolvedTo") != m)
    check(bool(_res) and not _wrong,
          "and each resolves to ITSELF, with no fallback to another module", str(_wrong))
    _all_empty = sorted(m for m in _res if _res[m].get("status") is None)
    check(bool(_res) and not _all_empty,
          "and NO module anywhere in the taxonomy resolves to an empty result against a "
          "server-shaped signal array", str(_all_empty[:8]))

print()
for f in _fail:
    print("FAIL:", f)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
