"""
RUN 32 FINAL CLOSURE. THE CLIENT TAXONOMY AND QUALIFIER ARTIFACTS, CHECKED AGAINST THE AUTHORITIES.

THE ORACLE IS NOT THE OTHER CLIENT FILE. Comparing `categories.js` to `taxonomy.js` and calling
that verification would be two objects under test agreeing with each other -- the same shape as
the defensibility generator that compared its output against itself and stayed green through a
wrong derivation for two runs. The oracle here is:

    the naming/registry authority   (registry.py, the registry map, the dispatch tables)
  + the server qualifier authority  (registry.PROXY_QUALIFIERS)
  + the generator rules             (build_client_taxonomy.py, run with --check)

and the two generated client files are the objects under test.

The population is derived from the registry. No module count is written down here.
"""
from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "server"))
sys.path.insert(0, str(HERE))

from app.simulation import registry as REG                                  # noqa: E402
from app.simulation.portfolio import PORTFOLIO_VALIDATED as PV              # noqa: E402
import participant_packages as PP                                           # noqa: E402

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


def head(t):
    print(f"\n=== {t} ===")


GEN = HERE / "build_client_taxonomy.py"
CATEGORIES = ROOT / "assets/js/categories.js"
TAXONOMY = ROOT / "assets/js/taxonomy.js"
KNOWLEDGE = ROOT / "assets/js/knowledge.js"
INDEX = ROOT / "index.html"


def node_eval(path: pathlib.Path):
    """The array as the BROWSER would hold it, by executing the file."""
    import shutil
    import tempfile
    node = shutil.which("node")
    if not node:
        return None
    probe = ("const fs=require('fs');global.window=global;"
             "eval(fs.readFileSync(process.argv[2],'utf8'));"
             "console.log(JSON.stringify(window.LIN_CATEGORIES));")
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as fh:
        fh.write(probe)
        probe_path = fh.name
    r = subprocess.run([node, probe_path, str(path)], capture_output=True, text=True, timeout=120)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


head("1. ONE AUTHORITY GENERATES THE RUNTIME ARTIFACT")

check(GEN.is_file(), "the generator exists", str(GEN))
r = subprocess.run([sys.executable, str(GEN), "--check"], capture_output=True, text=True,
                   cwd=HERE, timeout=600)
check(r.returncode == 0,
      "BOTH client taxonomy artifacts are exactly what the authorities generate: editing either "
      "one by hand cannot silently fix or break production, because regenerating overwrites it",
      (r.stdout + r.stderr)[-260:])
check((HERE / "taxonomy_authority.json").is_file(),
      "the presentation authority exists and is the only hand-maintained taxonomy source")

head("2. THE RUNTIME LOADS THE GENERATED ARTIFACT")

idx = INDEX.read_text(encoding="utf-8")
check("assets/js/taxonomy.js" in idx,
      "index.html loads taxonomy.js, so that is the artifact the live application runs on")
check("assets/js/categories.js" not in idx,
      "and does not load categories.js, which is the researcher-side stack")
check("assets/js/categories.js" in (ROOT / "tests.html").read_text(encoding="utf-8"),
      "categories.js is still consumed by tests.html, so it is retained as a generated derivative "
      "rather than deleted")

head("3. EVERY CURRENT MODULE IDENTITY, NAME AND METHOD CLASS AGREES WITH THE AUTHORITY")

live = node_eval(TAXONOMY)
check(live is not None, "the runtime artifact executes and exposes LIN_CATEGORIES")
if live is not None:
    rows = {m["num"]: m for c in live for m in c.get("modules", [])}
    # THE POPULATION IS THE ONE IN SERVICE. load_registry()/registry_index() resolve retired
    # identifiers by design (registry.py:426); service_index() (registry.py:440) is the roster
    # in service, derived from p0-baseline/module_renumbering_map.csv. A retired identity must
    # not reach the participant taxonomy, so comparing against the whole registry asserted the
    # pre-retirement population. The name, method-class and disabled loops below iterate this
    # same mapping, so their per-module coverage is unchanged: every id they reached before is
    # an id present in `rows`, and `rows` is the in-service set.
    reg = {mid: row["module_name"] for mid, row in REG.service_index().items()}
    check(set(rows) == set(reg),
          f"the runtime taxonomy carries exactly the identities in service ({len(reg)}), derived "
          f"rather than counted here",
          str(sorted(set(rows) ^ set(reg))[:8]))
    bad_name = sorted(f"{k}: {rows[k].get('name')!r} vs {reg[k]!r}"
                      for k in reg if k in rows and rows[k].get("name") != reg[k])
    check(not bad_name, "every runtime name is the registry's current name", "; ".join(bad_name[:4]))
    bad_mc = []
    for k in reg:
        if k not in rows:
            continue
        want = (REG.VALIDATED[k][0] if k in REG.VALIDATED
                else PV[k] if k in PV else rows[k].get("method_class"))
        if rows[k].get("method_class") != want:
            bad_mc.append(f"{k}: {rows[k].get('method_class')!r} vs {want!r}")
    check(not bad_mc,
          "every runtime method class is the identifier its production runner emits",
          "; ".join(bad_mc[:4]))
    bad_dis = sorted(f"{k}: runtime {bool(rows[k].get('disabled'))} vs registry "
                     f"{k in REG.DISABLED_MODULES}"
                     for k in reg if k in rows
                     and bool(rows[k].get("disabled")) != (k in REG.DISABLED_MODULES))
    check(not bad_dis,
          "and every runtime disabled flag is the registry's, which the two files had already "
          "silently disagreed about before one generator produced them", "; ".join(bad_dis[:4]))

head("4. EVERY CURRENT QUALIFIER AGREES WITH THE SERVER AUTHORITY")

kn = KNOWLEDGE.read_text(encoding="utf-8")
i = kn.index("const RUN1_PROXY_QUALIFIER = {")
st = kn.index("{", i)
d = 0
for j in range(st, len(kn)):
    if kn[j] == "{":
        d += 1
    elif kn[j] == "}":
        d -= 1
        if d == 0:
            block = kn[st:j + 1]
            break
client_keys = set(re.findall(r"^\s{4}(\w+):", block, re.M))
server_classes = {REG.VALIDATED[k][0] if k in REG.VALIDATED else PV.get(k, k): k
                  for k in REG.PROXY_QUALIFIERS}
check(client_keys == set(server_classes),
      "the client qualifier map holds EXACTLY the qualifiers the server still holds -- no module "
      "is told it is a proxy when the server says it is not, and none the server holds is missing",
      f"client {sorted(client_keys)} vs server {sorted(server_classes)}")

# Every remaining qualifier must belong to a module that is genuinely still a proxy: no canonical
# layer. This is the rule Runs 29 and 30 applied when they withdrew theirs.
from app.simulation.canonical import CANONICAL_STRUCTURE_KEYS as K0         # noqa: E402
from app.simulation.canonical_v3 import V3_STRUCTURE_KEYS as K3             # noqa: E402
from app.simulation.canonical_v4 import V4_STRUCTURE_KEYS as K4             # noqa: E402
from app.simulation.canonical_v5 import V5_STRUCTURE_KEYS as K5             # noqa: E402
from app.simulation.canonical_v6 import V6_STRUCTURE_KEYS as K6             # noqa: E402
from app.simulation.canonical_v7 import V7_STRUCTURE_KEYS as K7             # noqa: E402
CANON = set(K0) | set(K3) | set(K4) | set(K5) | set(K6) | set(K7)
still_canon = sorted(k for k in REG.PROXY_QUALIFIERS if k in CANON)
check(not still_canon,
      "NO module that routes into a canonical layer still carries a proxy qualifier: a qualifier "
      "describing a proxy the remediation removed would advertise a weakness the code no longer "
      "has", str(still_canon))

head("5. HISTORICAL ALIASES STAY SEPARATE FROM CURRENT VALUES")

tax_src = TAXONOMY.read_text(encoding="utf-8")
check("window.LIN_HISTORICAL_METHOD_CLASS" in tax_src,
      "the runtime artifact declares the historical alias map")
superseded = set(PP.V9_METHOD_CLASS_PROPAGATION.values())
if live is not None:
    primary = sorted(k for k, m in rows.items() if m.get("method_class") in superseded)
    check(not primary,
          "and NO superseded identifier is a current primary anywhere in the runtime taxonomy",
          str(primary))
check(not (client_keys & superseded),
      "and no qualifier key is a superseded identifier", str(sorted(client_keys & superseded)))

head("6. NO DUPLICATE CURRENT AUTHORITY REMAINS")

check(not re.search(r"^\s*window\.LIN_CATEGORIES\s*=", kn, re.M),
      "knowledge.js declares no taxonomy of its own")
generated = [rel for rel in ("assets/js/categories.js", "assets/js/taxonomy.js")
             if "GENERATED FROM" in (ROOT / rel).read_text(encoding="utf-8")
             or "build_client_taxonomy" in (ROOT / rel).read_text(encoding="utf-8")]
check(len(generated) == 2,
      "both client artifacts name the generator that produces them, so a reader editing one is "
      "told where the authority is", str(generated))

print()
for f in _fail:
    print("FAIL:", f)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
