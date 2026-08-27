#!/usr/bin/env python3
"""
RUN 71. THE INJECTION CAMPAIGN: every claim of the document control, proven by deleting its site.

STANDING RULE 9 AND 10. Each defect below is injected by deleting or corrupting THE EXACT LINE
the claim rests on — not a name matched file-wide — the bytes are RE-READ FROM DISK to confirm
the injection landed, the driver is re-run and must go RED for the intended check and for that
reason, and the file is restored inside a `finally` FROM A COMMITTED GIT OBJECT, never from a
snapshot of disk (Run 53 leaked a fault across five runs that way). A start-and-end
`git status --porcelain` comparison is the real guard, and it is asserted here.

argv[1] = the commit to snapshot the pristine files from (default HEAD)
"""
from __future__ import annotations
import os, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
REF = sys.argv[1] if len(sys.argv) > 1 else "HEAD"
SCR = pathlib.Path(os.environ["RUN71_SCRATCH"])


def git(*args) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True,
                          check=True).stdout


def porcelain() -> str:
    return git("status", "--porcelain")


def committed(rel: str) -> str:
    return git("show", f"{REF}:{rel}")


def run_driver(tag: str) -> tuple[int, str]:
    db = SCR / f"inj_{tag}.db"
    if db.exists():
        db.unlink()
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{db}", "RUN71_NO_BROWSER": "1"}
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"],
                   cwd=ROOT / "server", env=env, capture_output=True, text=True)
    p = subprocess.run([sys.executable, "tools/drive_run71_document_control.py",
                        f"inj-{tag}", str(SCR / f"inj_{tag}.json")],
                       cwd=ROOT / "server", env=env, capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def failed_checks(out: str) -> list[str]:
    return [ln.strip()[7:].split(" — ")[0].strip()
            for ln in out.splitlines() if ln.strip().startswith("[FAIL]")]


# (tag, file, the EXACT substring that is the site, what replaces it, which check must go RED)
INJECTIONS = [
    ("exclusion", "server/app/documents.py",
     "        if d.document_id in superseded or d.document_id in archived:",
     "        if d.document_id in superseded:",
     ["1b. every field the archived document supplied has left the live signal inputs"]),
    ("confirmation", "server/app/documents.py",
     '        return err("the confirmation shown to the person must be supplied and recorded")',
     "        confirmation = \"(none recorded)\"",
     ["5a. an archive request with no recorded confirmation is refused and archives nothing"]),
    ("audit", "server/app/documents.py",
     '    audit(session, "documents_archived", participant_id=caller.participant_id,',
     '    _unused = dict(  # INJECTED: the audit row is not written\n'
     '          participant_id=caller.participant_id,',
     ["6. the archive record names the document, the period, the time and the fields withdrawn"]),
    ("fields", "server/app/documents.py",
     '            fields = sorted({str(o.get("field")) for o in emit_observations(entry)\n'
     '                             if o.get("field")})',
     "            fields = []",
     ["6. the archive record names the document, the period, the time and the fields withdrawn"]),
    ("bytes", "server/app/documents.py",
     "        row.archived_at = now\n        row.archived_by = caller.participant_id",
     "        row.archived_at = now\n        row.archived_by = caller.participant_id\n"
     "        _d = session.get(Document, doc_id)\n        _d.content = b''"
     "  # INJECTED: destroy the bytes",
     ["3. the archived document's bytes read back intact from the archive"]),
]

START = porcelain()
print("=" * 96)
print(f"snapshot reference: {REF}   git status --porcelain at start:\n{START or '  (clean)'}")
print("=" * 96)

base_rc, base_out = run_driver("baseline")
base_fail = failed_checks(base_out)
print(f"BASELINE: exit {base_rc}, failures {base_fail}")
assert base_rc == 0 and not base_fail, "baseline is not green; the campaign cannot run"

rows = []
for tag, rel, site, replacement, expect in INJECTIONS:
    path = ROOT / rel
    pristine = committed(rel)
    try:
        disk = path.read_text()
        assert site in disk, f"{tag}: the site is not on disk — the check is not pinned to it"
        path.write_text(disk.replace(site, replacement, 1))
        # RE-READ FROM DISK: the injection must be provably present, not merely written.
        # THE INJECTION IS PROVEN PRESENT, not assumed. Some injections DELETE the site and
        # some APPEND to it, so "the site is gone" is not the test: the test is that the exact
        # replacement text is on disk and the file differs from what it was.
        after = path.read_text()
        landed = replacement in after and after != disk
        rc, out = run_driver(tag)
        got = failed_checks(out)
        red_for_reason = all(any(e in g for g in got) for e in expect)
        rows.append((tag, landed, rc != 0, red_for_reason, got))
        print("-" * 96)
        print(f"INJECTION {tag}: landed={landed}  driver_exit={rc}  RED_for_the_intended_reason="
              f"{red_for_reason}")
        print(f"  expected RED: {expect}")
        print(f"  observed RED: {got}")
    finally:
        path.write_text(pristine)
        assert path.read_text() == pristine, f"{tag}: restore did not land"

END = porcelain()
print("=" * 96)
print(f"git status --porcelain at end:\n{END or '  (clean)'}")
green_rc, green_out = run_driver("restored")
green_fail = failed_checks(green_out)
print(f"AFTER RESTORE: exit {green_rc}, failures {green_fail}")
ok = (START == END and green_rc == 0 and not green_fail
      and all(landed and red and reason for _t, landed, red, reason, _g in rows))
print("-" * 96)
for t, landed, red, reason, got in rows:
    print(f"  {t:14} landed={landed!s:5} went_red={red!s:5} for_the_right_reason={reason!s:5}")
n = len(rows) + 3
passed = n - (0 if START == END else 1) - (0 if green_rc == 0 and not green_fail else 1) \
         - (0 if base_rc == 0 else 1) - sum(0 if (l and r and rs) else 1
                                            for _t, l, r, rs, _g in rows)
print(f"RESULT: {passed}/{n} checks passed")
raise SystemExit(0 if ok else 1)
