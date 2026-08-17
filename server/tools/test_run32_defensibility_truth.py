"""
RUN 32 FINAL CLOSURE. THE SERVED DEFENSIBILITY OBJECT, CHECKED AGAINST THE RUNNING INSTRUMENT.

WHAT MAKES THIS GUARD DIFFERENT FROM THE ONE BESIDE IT. `test_run11_defensibility_claims.py`
re-runs the generator and compares its output to the committed file byte for byte. That proves the
file was not hand-edited. It CANNOT prove the file is true, because the generator produces both
sides: if the generator's derivation is wrong, the committed file matches it perfectly and the
check stays green. That is exactly what happened -- for two runs the generator read four of the
six canonical structure maps, and twenty-two modules were served the sentence "not required by
this module" about a governed structure their production routes required, with every existing
guard green throughout.

SO THIS ONE NEVER READS THE GENERATOR. It rebuilds the expected inventory INDEPENDENTLY from the
running instrument -- registry identity, activation, dispatch tables, the structure maps of every
canonical layer, the production intake vocabulary, and the runner resolved through `__wrapped__`
past the Category-9 boundary -- and compares the SERVED OBJECT against that. Comparing it against
another copied metadata table would be the failure mode this repository already knows: asserting
against a copy of the logic.

The population is derived from the registry. No module count is written down here.
"""

from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(HERE))

_spec = importlib.util.spec_from_file_location(
    "run32_inventory", HERE / "build_run32_defensibility_inventory.py")
INV = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(INV)

from app.simulation import registry as REG                                 # noqa: E402

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


def head(t: str) -> None:
    print(f"\n=== {t} ===")


head("1. POPULATION: the served object covers exactly the current registry, derived")

reg = REG.load_registry()
ids = [m["new_id"] for m in reg]
served = INV.served()
check(len(ids) == len(set(ids)), "the registry declares no duplicate identity",
      str(sorted({i for i in ids if ids.count(i) > 1})))
missing = sorted(set(ids) - set(served))
extra = sorted(set(served) - set(ids))
check(not missing, "every current registry identity has a served defensibility record",
      str(missing))
check(not extra, "and the served object invents no module the registry does not declare",
      str(extra))
check(len(served) == len(ids),
      f"the two populations are the same size, derived from the registry rather than written "
      f"down here ({len(ids)})", f"served {len(served)} vs registry {len(ids)}")

head("2. EVERY SERVED STATEMENT IS THE ONE THE INSTRUMENT SUPPORTS")

wrong_name, wrong_exec, wrong_state, wrong_struct, wrong_req, wrong_runner = [], [], [], [], [], []
for m in reg:
    mid, name = m["new_id"], m["module_name"]
    s = served.get(mid)
    if s is None:
        continue
    e = INV.expected_for(mid, name)
    if s.get("name") != name:
        wrong_name.append(f"{mid}: served {s.get('name')!r} vs registry {name!r}")
    if s.get("implementation") != e["execution"]:
        wrong_exec.append(f"{mid}: served {str(s.get('implementation'))[:60]!r}")
    if s.get("operationalState") != INV.state_of(e):
        wrong_state.append(f"{mid}: served {s.get('operationalState')!r} vs {INV.state_of(e)!r}")
    if s.get("canonicalStructure") != e["structure_stmt"]:
        wrong_struct.append(f"{mid}: served {str(s.get('canonicalStructure'))[:50]!r}")
    want_req = e["structure_stmt"] == INV.STRUCT_REQUIRED
    if bool(s.get("canonicalStructureRequired")) != want_req:
        wrong_req.append(f"{mid}: served {s.get('canonicalStructureRequired')} vs {want_req}")
    if s.get("canonicalRunner") != e["runner"]:
        wrong_runner.append(f"{mid}: served {str(s.get('canonicalRunner'))[:60]!r} "
                            f"vs {e['runner']!r}")

check(not wrong_name, "every served name is the registry's own current name for that identity",
      "; ".join(wrong_name[:3]))
check(not wrong_exec,
      "every served execution statement is the one the module's current route supports: a module "
      "that does not currently produce a project reading is never described as computing one",
      "; ".join(wrong_exec[:3]))
check(not wrong_state, "every served operationalState matches the derived state",
      "; ".join(wrong_state[:3]))
check(not wrong_struct,
      "every served canonical-structure sentence matches what the current production route "
      "actually requires, derived from every canonical layer's structure map",
      "; ".join(wrong_struct[:3]))
check(not wrong_req,
      "and the machine-readable canonicalStructureRequired agrees with it, so a reader and a "
      "program cannot be told different things", "; ".join(wrong_req[:3]))
check(not wrong_runner,
      "every served canonicalRunner is the implementation a production dispatch actually reaches, "
      "resolved past the qualification boundary rather than at the wrapper",
      "; ".join(wrong_runner[:3]))

head("3. THE STATES THE OBJECT MUST BE ABLE TO TELL APART")

by_state: dict[str, list[str]] = {}
for mid, s in served.items():
    by_state.setdefault(str(s.get("operationalState")), []).append(mid)
for state in ("COMPUTES_FROM_AVAILABLE_EVIDENCE", "CONDITIONAL_ON_GOVERNED_STRUCTURE",
              "DISABLED_CONCEPT_ONLY", "ARCHIVED_FUTURE_RESEARCH", "SUPPLIED_VALUE",
              "PORTFOLIO_COMPUTED", "DISABLED_EVIDENCE_UNDER_REVIEW"):
    check(bool(by_state.get(state)),
          f"the object distinguishes {state} and at least one module carries it",
          str(sorted(by_state)))
check(not any("computed by the server" in str(s.get("implementation")) for s in served.values()),
      "NO module is described with the old single generic sentence 'computed by the server', "
      "which was being used for seven different situations at once")

head("4. THE NAMED CASES THE CLOSURE CONTRACT CALLS OUT")

def state(mid: str) -> str:
    return str(served.get(mid, {}).get("operationalState"))

check(state("B2.9") == "ARCHIVED_FUTURE_RESEARCH",
      "B2.9 Quantum Probability is served as archived research and not as a runnable capability",
      state("B2.9"))
check(state("A4.1") == "SUPPLIED_VALUE",
      "A4.1 Document Risk Score is served as a supplied value and not as a server computation",
      state("A4.1"))
check(state("A3.4") == "DISABLED_EVIDENCE_UNDER_REVIEW",
      "A3.4 Material Cost Variance is served as disabled pending an evidence-design decision",
      state("A3.4"))
for _mid in sorted(INV.K7):
    check(state(_mid) == "CONDITIONAL_ON_GOVERNED_STRUCTURE"
          or _mid in REG.DISABLED_MODULES,
          f"{_mid} is served as conditional on its governed decision structure, or as disabled",
          state(_mid))
check(served.get("B4.7", {}).get("definingStructure") == "actionScenarioMatrix",
      "B4.7 names the action-by-scenario matrix it requires, so 'Not Estimable' has a reason a "
      "reader can check", str(served.get("B4.7", {}).get("definingStructure")))

head("5. THE CLIENT TAXONOMY CARRIES THE CURRENT IDENTITY, NOT A SUPERSEDED ONE")

# The participant-facing taxonomy is a separate surface from the defensibility object and drifted
# separately, so it is checked against the registry directly rather than against that object.
for rel in ("assets/js/categories.js", "assets/js/taxonomy.js"):
    txt = (ROOT / rel).read_text(encoding="utf-8")
    m = re.search(r"num: 'B4\.7', name: '([^']*)', method_class: '([^']*)'", txt)
    check(m is not None, f"{rel}: the B4.7 taxonomy row is present and parseable")
    if m:
        want_name = next(r["module_name"] for r in reg if r["new_id"] == "B4.7")
        check(m.group(1) == want_name,
              f"{rel}: B4.7's displayed name is the registry's current name", m.group(1))
        check(m.group(2) == REG.VALIDATED["B4.7"][0],
              f"{rel}: and its method class is the identifier the runner actually emits",
              m.group(2))

head("6. THE METHOD-HELP ENTRIES CARRY NO LEGACY PROXY DESCRIPTION")

# The handbook's Category-10 entries described the v19 PROXIES as current, and their band ladders
# named a status colour those modules do not emit. That surface renders only inside an
# authenticated participant session, and its module array is local to knowledge.js rather than
# exposed on `window`, so the browser verification cannot reach it. It is guarded HERE instead,
# against the canonical layer, rather than being left to a source edit nothing checks.
_kn = (ROOT / "assets" / "js" / "knowledge.js").read_text(encoding="utf-8")
_LEGACY_DESCRIPTIONS = {
    "B4.1": "normalises cost performance",
    "B4.2": "remaining work and remaining budget",
    "B4.3": "four fixed governance constraints",
    "B4.4": "Projects four explicit named futures",
    "B4.5": "which single input",
    "B4.6": "cost/schedule/risk Pareto frontier",
    "B4.7": "monitor/investigate/escalate",
}
for _mid, _legacy in sorted(_LEGACY_DESCRIPTIONS.items()):
    _i = _kn.index(f'{{ n: "{_mid}"')
    _j = _kn.index('{ n: "', _i + 10) if '{ n: "' in _kn[_i + 10:] else len(_kn)
    _entry = _kn[_i:_j]
    check(_legacy not in _entry,
          f"{_mid}: the handbook no longer describes the superseded v19 proxy as the current "
          f"method", _legacy)
    check("bands:" not in _entry,
          f"{_mid}: and carries no Red/Amber/Green ladder, because this module emits no status "
          f"colour and cannot reach the governed status")
    _want_mc = REG.VALIDATED[_mid][0]
    check(f'mc: "{_want_mc}"' in _entry,
          f"{_mid}: and its handbook method class is the identifier the runner emits", _want_mc)

print()
for f in _fail:
    print("FAIL:", f)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
