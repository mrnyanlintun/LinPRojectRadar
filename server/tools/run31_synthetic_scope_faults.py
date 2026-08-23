#!/usr/bin/env python3
"""Section 5: the four synthetic-scope non-vacuity faults. A crash is never RED."""
import os, pathlib, re, shutil, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# --- CAMPAIGN SAFETY (Run 54, phase A) -----------------------------------------------------
# THE START-AND-END DIRTY-TREE GUARD. A campaign must not BEGIN on a dirty tree: Run 53
# established that a leaked fault is snapshotted from disk by the next campaign, faithfully
# restored by its `finally`, and thereby CERTIFIED by its own passing assertion. An end-only
# check cannot see that, because the leak began in an earlier process. See
# server/tools/campaign_safety.py for the full mechanism and the proof.
import sys as _cs_sys, pathlib as _cs_pl                                       # noqa: E402
_cs_sys.path.insert(0, str(_cs_pl.Path(ROOT) / "server" / "tools"))
from campaign_safety import (arm as _cs_arm, restore_guard, head_text,          # noqa: E402,F401
                             snapshot_text, CampaignTreeDirty)
_cs_arm(_cs_pl.Path(ROOT), "run31_synthetic_scope_faults.py",
        allow=[])
# -------------------------------------------------------------------------------------------
SYNTH = ROOT / "research_fixtures" / "synthetic"
SCOPE = HERE / "build_run31_synthetic_scope.py"
SWEEP = HERE / "test_run31_synthetic_checksums.py"


def run(name):
    tmp = tempfile.mkdtemp()
    db = pathlib.Path(tmp) / "t.db"
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT / "server",
                   env={**os.environ, "DATABASE_URL": f"sqlite:///{db}"}, capture_output=True)
    out = subprocess.run([sys.executable, f"{name}.py"], cwd=HERE,
                         env={**os.environ, "DATABASE_URL": f"sqlite:///{db}",
                              "SESSION_SECRET": "x", "PYTHONIOENCODING": "utf-8"},
                         capture_output=True, text=True)
    m = re.search(r"^RESULT: (\d+)/(\d+)", out.stdout, re.M)
    return (int(m.group(1)), int(m.group(2))) if m else (0, 0)


def scope_counts():
    r = subprocess.run([sys.executable, str(SCOPE)], cwd=HERE, capture_output=True, text=True,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    g = lambda pat: int(re.search(pat, r.stdout).group(1)) if re.search(pat, r.stdout) else -1
    return {"missing": g(r"MISSING local entries\s+=\s+(\d+)"),
            "mismatch": g(r"checksum mismatches\s+=\s+(\d+)"),
            "external": g(r"external entries\s+Y = (\d+)"),
            "unclassified": g(r"unclassified\s+=\s+(\d+)")}


GUARD = "test_run31_synthetic_checksums"
base_p, base_t = run(GUARD)
base_scope = scope_counts()
print(f"BASELINE  {GUARD}: {base_p}/{base_t} green={base_p==base_t}  scope={base_scope}\n")

TARGET = SYNTH / "OG-SYNTH-0.1" / "package_A" / "package_A_project_structures"
victim = next(TARGET.rglob("*.csv"))
rows = []


def record(n, desc, landed, p, t, scope, reason):
    crashed = (t == 0)
    red = (p != t) and not crashed
    verdict = "CRASH (not RED)" if crashed else ("RED" if red else "STILL GREEN")
    print(f"FAULT {n}: {desc}\n  landed={landed}  {GUARD}: {p}/{t} -> {verdict}\n  scope={scope}\n"
          f"  ({reason})\n")
    rows.append((n, landed, red, verdict))


# --- A: remove one locally governed package file -------------------------------------------
backup = victim.read_bytes()
victim.unlink()
landed = not victim.is_file()
p, t = run(GUARD)
record("A", f"remove a locally governed file ({victim.name})", landed, p, t, scope_counts(),
       "the sweep must report it missing rather than passing over it")
victim.write_bytes(backup)

# --- D: mutate one resolved local package byte ----------------------------------------------
victim.write_bytes(backup + b"\n# RUN31 MUTATION\n")
landed = victim.read_bytes() != backup
p, t = run(GUARD)
record("D", f"mutate a resolved local byte ({victim.name})", landed, p, t, scope_counts(),
       "the checksum guard must reject the changed file")
victim.write_bytes(backup)

# --- B: misclassify a locally governed file as external -------------------------------------
src = SCOPE.read_text()
gov = "package_A_project_structures/" + str(victim.relative_to(TARGET))
mut = src.replace('KNOWN_UNDELIVERED_BY_PROGRAMME = {"OG-SYNTH-0.1": set(CLAIMED_NEVER_DELIVERED)}',
                  'KNOWN_UNDELIVERED_BY_PROGRAMME = {"OG-SYNTH-0.1": set(CLAIMED_NEVER_DELIVERED) | {"%s"}}' % gov)
SCOPE.write_text(mut)
sweep_src = SWEEP.read_text()
SWEEP.write_text(sweep_src.replace(
    '        "schemas/schema_catalog.json",\n    },',
    '        "schemas/schema_catalog.json",\n        "%s",\n    },' % gov))
landed = gov in SCOPE.read_text() and gov in SWEEP.read_text()
sc = scope_counts()
# THE GUARD IS THE SWEEP'S SCOPE-AUTHORITY CHECK, which compares the committed never-delivered
# set against the tree: a file that is PRESENT may not be declared never-delivered.
gp, gt = run(GUARD)
red_b = (gp != gt) and gt > 0
print(f"FAULT B: misclassify a locally governed file as external\n  landed={landed}  "
      f"{GUARD}: {gp}/{gt}  scope={sc}\n  -> {'RED' if red_b else 'STILL GREEN'}\n"
      f"  (a present, checksum-matching file may not be declared external)\n")
rows.append(("B", landed, red_b, "RED" if red_b else "STILL GREEN"))
SCOPE.write_text(src)
SWEEP.write_text(sweep_src)

# --- C: misclassify an external reference as locally preserved without supplying the file ----
mut = src.replace('    "schemas/schema_catalog.json":\n', '    "FAULT_C_REMOVED_schema_catalog.json":\n')
SCOPE.write_text(mut)
landed = "FAULT_C_REMOVED" in SCOPE.read_text()
sc = scope_counts()
red_c = sc["unclassified"] > base_scope["unclassified"]
print(f"FAULT C: claim an undelivered file is locally preserved, without supplying it\n"
      f"  landed={landed}  scope={sc}\n  -> {'RED' if red_c else 'STILL GREEN'}\n"
      f"  (an entry with no committed authority must be reported UNCLASSIFIED, not passed)\n")
rows.append(("C", landed, red_c, "RED" if red_c else "STILL GREEN"))
SCOPE.write_text(src)

p, t = run(GUARD)
print(f"RESTORED  {GUARD}: {p}/{t} green={p==t}  scope={scope_counts()}")
ok = sum(1 for _n, l, r, _v in rows if l and r)
print(f"\nfaults={len(rows)} applied={sum(1 for _n,l,_r,_v in rows if l)} "
      f"RED={sum(1 for _n,_l,r,_v in rows if r)} PASS={ok}/{len(rows)} "
      f"crashes_scored_RED={sum(1 for _n,_l,_r,v in rows if 'CRASH' in v)}")
