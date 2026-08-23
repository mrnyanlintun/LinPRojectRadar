"""
RUN 32 FINAL CLOSURE. THE FOURTEEN-FAULT NON-VACUITY CAMPAIGN.

The defects this closure removed were all invisible behind green suites: a client qualifier map
that had drifted to twenty-nine keys against the server's five, two hand-maintained taxonomies
that had silently diverged, and a per-module handbook surface that two closures recorded as
unreachable because the navigation was wrong. So every guard is broken on purpose here.

Discipline, unchanged: a crash is NOT red; an unrelated failure is not evidence; the mutation is
verified by re-reading the bytes from disk; __pycache__ is cleared on both sides; every file is
restored byte for byte and the baseline re-run and required green.

Writes code_audit/run32_qualifier_fault_injection.csv.
"""
from __future__ import annotations

import csv, os, pathlib, re, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
SERVER = HERE.parent
ROOT = SERVER.parent

AUTH = "test_run32_client_authority.py"
MC = "test_run32_method_class_agreement.py"
PKG = "test_run28_participant_packages.py"
DEFENS = "test_run32_defensibility_truth.py"
SURFACE = "test_run32_handbook_surface.py"

REGISTRY = SERVER / "app/simulation/registry.py"
KNOWLEDGE = ROOT / "assets/js/knowledge.js"
TAXONOMY = ROOT / "assets/js/taxonomy.js"
CATEGORIES = ROOT / "assets/js/categories.js"
AUTHORITY = HERE / "taxonomy_authority.json"
INDEX = ROOT / "index.html"
V9 = ROOT / "code_audit/run32_b3_participant_package_v9_checksums.sha256"


def clear_pycache():
    for d in SERVER.rglob("__pycache__"):
        shutil.rmtree(d, ignore_errors=True)


_T = None


def template_db():
    global _T
    if _T is None:
        tmp = pathlib.Path(tempfile.mkdtemp(prefix="run32qual-"))
        db = tmp / "t.db"
        env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}", SESSION_SECRET="test-secret")
        r = subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                           cwd=SERVER, env=env, capture_output=True, text=True)
        if r.returncode:
            raise SystemExit("alembic failed:\n" + r.stdout + r.stderr)
        _T = db
    return _T


def run_guard(suite):
    t = template_db()
    db = t.parent / f"{suite}.{os.getpid()}.db"
    shutil.copy(t, db)
    env = dict(os.environ, DATABASE_URL=f"sqlite:///{db}", SESSION_SECRET="test-secret",
               PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, suite], cwd=HERE, env=env,
                       capture_output=True, text=True, timeout=1800)
    out = (r.stdout or "") + (r.stderr or "")
    res = None
    for ln in out.splitlines():
        s = ln.strip()
        if s.startswith("RESULT: ") and "/" in s:
            res = s
    db.unlink(missing_ok=True)
    return r.returncode, out, res


def failing_lines(out):
    L = []
    for raw in out.splitlines():
        s = raw.strip()
        if s.startswith(("FAIL: ", "FAILED: ")):
            L.append(s.split(": ", 1)[1])
        elif s.startswith("FAIL "):
            L.append(s[5:])
        elif s.startswith("**** "):
            L.append(s[5:].strip())
        elif s.startswith("- "):
            L.append(s[2:])
    return L


def is_green(res):
    if not res:
        return False
    a, b = res.split("RESULT: ", 1)[1].split()[0].split("/")
    return a == b


def faults():
    F = []
    A = F.append
    # 1 -- a current server qualifier omitted from the client generation.
    A((1, "assets/js/knowledge.js RUN1_PROXY_QUALIFIER",
       "the client map holds exactly the qualifiers the server still holds",
       KNOWLEDGE, "    CUSUM: \"hard-coded transformations", "    CUSUM_OMITTED: \"hard-coded transformations",
       AUTH, "the client qualifier map holds EXACTLY the qualifiers the server still holds"))
    # 2 -- a withdrawn qualifier restored as current.
    A((2, "assets/js/knowledge.js RUN1_PROXY_QUALIFIER",
       "no module that routes into a canonical layer carries a proxy qualifier",
       KNOWLEDGE, "    Portfolio_Outlier:",
       "    Constraint_Satisfaction: \"an explainable four-rule checklist, not a "
       "constraint-satisfaction solver\",\n    Portfolio_Outlier:",
       AUTH, "the client qualifier map holds EXACTLY the qualifiers the server still holds"))
    # 3 -- a historical-only qualifier exposed on the current UI (a superseded identifier as a key).
    A((3, "assets/js/knowledge.js RUN1_PROXY_QUALIFIER",
       "no qualifier key is a superseded identifier",
       KNOWLEDGE, "    Portfolio_Outlier:",
       "    Contract_Mod_Frequency: \"a raw modification count\",\n    Portfolio_Outlier:",
       AUTH, "the client qualifier map holds EXACTLY the qualifiers the server still holds"))
    # 4 -- a current method-class key changed back to a stale identifier.
    A((4, "assets/js/taxonomy.js B3.2 row",
       "every runtime method class is the identifier its production runner emits",
       TAXONOMY, "method_class: 'EVMS_Applicability'", "method_class: 'FAR_Threshold'",
       MC, "no module carries a method class its production runner has stopped emitting"))
    # 5 -- a current lookup silently returns an empty result.
    A((5, "assets/js/taxonomy.js numForMethodClass",
       "the status lookup resolves rather than silently returning null",
       TAXONOMY, "    var num = METHOD_TO_NUM[methodClass];\n    if (num) return num;",
       "    var num = undefined;\n    if (num) return num;",
       MC, "and no module's status resolves to a silent null against a row that contains it"))
    # 6 -- a lookup falls back to another module's qualifier.
    A((6, "assets/js/taxonomy.js numForMethodClass",
       "a method class resolves to ITS OWN module and never to another",
       # The primary lookup is redirected, so EVERY class resolves to A1.10's number. The alias
       # branch alone is never reached for a current identifier, which is why mutating it there
       # left the guard green in the first pass -- the campaign refusing to credit that is the
       # rule working.
       TAXONOMY, "    var num = METHOD_TO_NUM[methodClass];\n    if (num) return num;",
       "    var num = METHOD_TO_NUM['CPI_Shrinkage_Forecast'];\n    if (num) return num;",
       MC, "and every stored-row lookup returns THAT module's row, never another's"))
    # 7 -- authority source changes but the runtime artifact is not regenerated.
    A((7, "server/tools/taxonomy_authority.json",
       "the runtime artifact is exactly what the authorities generate",
       AUTHORITY, '"color": "#4ea0ff"', '"color": "#000001"',
       AUTH, "BOTH client taxonomy artifacts are exactly what the authorities generate"))
    # 8 -- the two generated files disagree.
    A((8, "assets/js/categories.js versus taxonomy.js",
       "both artifacts are generated from the same authorities, so they cannot disagree",
       CATEGORIES, "module_id: 'A1.7', name: 'TCPI'", "module_id: 'A1.7', name: 'TCPI DRIFTED'",
       AUTH, "BOTH client taxonomy artifacts are exactly what the authorities generate"))
    # 9 -- the live application loads a stale, non-authoritative artifact.
    A((9, "index.html script imports",
       "index.html loads the generated runtime artifact and not the researcher-side stack",
       INDEX, '<script src="assets/js/taxonomy.js"></script>',
       '<script src="assets/js/categories.js"></script>',
       AUTH, "index.html loads taxonomy.js, so that is the artifact the live application runs on"))
    # 10 -- a current registry module omitted from generated metadata.
    A((10, "server/tools/taxonomy_authority.json",
        "the runtime taxonomy carries exactly the registry's identities",
        AUTHORITY, '"module_id": "A1.7",', '"module_id": "A1.7-GONE",',
        AUTH, "BOTH client taxonomy artifacts are exactly what the authorities generate"))
    # 11 -- a fake module added to generated metadata.
    A((11, "server/tools/taxonomy_authority.json",
        "the runtime taxonomy invents no module the registry does not declare",
        AUTHORITY, '{\n    "id": "a1_7",',
        '{\n    "id": "zz_9", "module_id": "Z9.9", "active": true, "required": []\n   },\n   {\n    "id": "a1_7",',
        AUTH, "BOTH client taxonomy artifacts are exactly what the authorities generate"))
    # 12 -- a required current handbook surface becomes unreachable.
    A((12, "assets/js/knowledge.js MODREF topic registration",
        "the per-module handbook surface is reachable and renders every module",
        KNOWLEDGE, '      if (MODREF_TOPICS[id]) return MODREF_TOPICS[id];',
        '      if (false) return MODREF_TOPICS[id];',
        SURFACE, "the per-module handbook surface resolves its module-reference topics"))
    # 13 -- a nonexistent handbook surface is marked verified.
    A((13, "server/tools/test_run32_handbook_surface.py",
        "a surface is only verified by reaching it; a claim that a nonexistent topic renders "
        "must fail",
        HERE / "test_run32_handbook_surface.py", 'MODREF_PREFIXES = (', 'MODREF_PREFIXES = ("cat99-modules",) + (',
        SURFACE, "every declared module-reference topic exists in the handbook"))
    # 14 -- a participant predecessor package regenerated after current-byte changes.
    import hashlib
    old_line = [l for l in V9.read_text(encoding="utf-8").splitlines()
                if l.strip().endswith("assets/js/knowledge.js")][0]
    live = hashlib.sha256((ROOT / "assets/js/knowledge.js").read_bytes()).hexdigest()
    A((14, "og-participant-2026.08-v9, a predecessor record",
        "a predecessor package is never regenerated to match the current tree",
        V9, old_line, f"{live}  assets/js/knowledge.js", PKG,
        "every one of v9's seventy checksums holds against commit"))
    return F


def main():
    HDR = ["fault_id", "module/system", "invariant", "baseline command", "mutation target",
           "mutation description", "mutation applied?", "fault command", "process exit code",
           "anchored RESULT present?", "expected RED reason", "actual RED reason", "crash?",
           "unrelated failure?", "restored?", "restored GREEN?", "final status", "notes"]
    rows, t = [], dict(att=0, app=0, red=0, rest=0, na=0, crash=0, unrel=0)
    for fid, system, inv, target, old, new, guard, reason in faults():
        t["att"] += 1
        cmd = f"cd server/tools && python3 {guard}"
        clear_pycache()
        brc, bout, bres = run_guard(guard)
        if not is_green(bres):
            rows.append([fid, system, inv, cmd, str(target), "-", "NO", cmd, brc,
                         "YES" if bres else "NO", reason, "-", "NO", "NO", "n/a", "NO",
                         "NOT_ATTEMPTED_BASELINE_RED", f"baseline not green ({bres})"])
            t["na"] += 1
            continue
        baseline = bres
        orig = target.read_bytes()
        text = orig.decode("utf-8")
        if text.count(old) != 1:
            rows.append([fid, system, inv, cmd, str(target.relative_to(ROOT)),
                         "anchor not unique", "NO", cmd, "-", "YES", reason, "-", "NO", "NO",
                         "n/a", "n/a", "NOT_APPLIED", f"anchor occurs {text.count(old)} times"])
            t["na"] += 1
            continue
        clear_pycache()
        target.write_bytes(text.replace(old, new, 1).encode("utf-8"))
        disk = target.read_bytes().decode("utf-8")
        if not (new in disk and disk != text):
            target.write_bytes(orig)
            clear_pycache()
            rows.append([fid, system, inv, cmd, str(target.relative_to(ROOT)), "byte replacement",
                         "NO", cmd, "-", "YES", reason, "-", "NO", "NO", "YES", "n/a",
                         "NOT_APPLIED", "mutation did not survive a re-read from disk"])
            t["na"] += 1
            continue
        t["app"] += 1
        frc, fout, fres = run_guard(guard)
        crash = fres is None
        red = fres is not None and not is_green(fres)
        fails = failing_lines(fout)
        intended = red and any(reason.strip().lower() in f.strip().lower() for f in fails)
        actual = ("no RESULT line (crash)" if crash else
                  ("; ".join(dict.fromkeys(f.strip()[:100] for f in fails)) or fres) if red
                  else "GREEN - guard did not notice")
        clear_pycache()
        target.write_bytes(orig)
        restored = target.read_bytes() == orig
        clear_pycache()
        rrc, rout, rres = run_guard(guard)
        rgreen = is_green(rres) and rres == baseline
        notes = []
        if crash:
            t["crash"] += 1
            status = "CRASH_NOT_ACCEPTED_AS_RED"
            notes.append("guard died without an anchored RESULT line; a crash is NOT red")
        elif not red:
            status = "GUARD_DID_NOT_FIRE"
            notes.append("guard stayed green under the mutation")
        elif not intended:
            t["unrel"] += 1
            status = "RED_FOR_AN_UNRELATED_REASON"
            notes.append("red, but its output did not name the intended property")
        else:
            t["red"] += 1
            status = "RED_FOR_THE_INTENDED_REASON"
        if rgreen:
            t["rest"] += 1
        else:
            notes.append(f"baseline did not return to {baseline} (got {rres})")
        rows.append([fid, system, inv, cmd, str(target.relative_to(ROOT)),
                     f"replace {old.strip().splitlines()[0][:60]!r}", "YES", cmd, frc,
                     "NO" if crash else "YES", reason, actual, "YES" if crash else "NO",
                     "YES" if (red and not intended) else "NO", "YES" if restored else "NO",
                     "YES" if rgreen else "NO", status, "; ".join(notes) or "clean"])
        print(f"fault {fid:2d}  {status:32s}  {actual[:76]}")
    out = ROOT / "code_audit" / "run32_qualifier_fault_injection.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(HDR)
        w.writerows(rows)
    print()
    print("attempted", t["att"], "| applied", t["app"], "| intended RED", t["red"],
          "| restored GREEN", t["rest"])
    print("NOT_APPLIED", t["na"], "| crashes accepted as RED 0 (%d recorded)" % t["crash"],
          "| unrelated accepted as RED 0 (%d recorded)" % t["unrel"])
    print("wrote", out.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
