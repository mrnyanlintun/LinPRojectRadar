"""Run 32 accounting closure: four-fault non-vacuity campaign.

Each fault is applied alone to a byte-restored tree. The guard must go RED **for the intended
reason** -- matched against the guard's OWN failing check sentences, never against this file's
prose -- and must return GREEN once the bytes are restored. A crash is not RED.
"""
import csv, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GUARD = os.path.join(ROOT, "server", "tools", "test_run32_qualifier_count_closure.py")
RECON = os.path.join(ROOT, "code_audit", "run32_proxy_qualifier_reconciliation.csv")
BUILDER = os.path.join(ROOT, "server", "tools", "build_run32_qualifier_count_closure.py")
OUT = os.path.join(ROOT, "code_audit", "run32_qualifier_count_fault_injection.csv")


def run_guard():
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, GUARD], cwd=ROOT, capture_output=True, env=env)
    out = (p.stdout + p.stderr).decode("utf-8", "replace")
    m = re.search(r"^RESULT: (\d+)/(\d+)", out, re.M)
    if m is None:
        return "CRASH", out, []
    failing = re.findall(r"^FAIL: (.+)$", out, re.M)
    return ("GREEN" if m.group(1) == m.group(2) else "RED"), out, failing


def clear_pycache():
    for base, dirs, _ in os.walk(os.path.join(ROOT, "server")):
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(base, d), ignore_errors=True)


# --- mutations: each returns (path, original_bytes) -------------------------------------------
def f_remove_row(path=RECON):
    b = open(path, "rb").read()
    lines = b.split(b"\n")
    del lines[2]
    open(path, "wb").write(b"\n".join(lines))
    return path, b


def f_duplicate_row(path=RECON):
    b = open(path, "rb").read()
    lines = b.split(b"\n")
    lines.insert(2, lines[1])
    open(path, "wb").write(b"\n".join(lines))
    return path, b


def f_fake_key(path=RECON):
    """Insert a row naming a qualifier key the pre-change map never held.

    Written through the csv module so the fabricated key lands in the qualifier-key COLUMN;
    a textual substitution hits the method-class column first and produces a duplicate key
    rather than an extra one, which is a different fault from the one intended here.
    """
    b = open(path, "rb").read()
    text = b.decode("utf-8")
    rows = list(csv.reader(text.splitlines()))
    header = rows[0]
    col = header.index("client qualifier key")
    fake = list(rows[1])
    fake[col] = "Fabricated_Qualifier_Key"
    rows.insert(2, fake)
    with open(path, "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerows(rows)
    return path, b


def f_suppress_key(path=BUILDER):
    b = open(path, "rb").read()
    t = b.decode("utf-8")
    anchor = "            entries.append({\"key\": m.group(1), \"value\": value, \"line\": n})"
    assert anchor in t, "suppression anchor not found"
    t = t.replace(anchor,
                  "            if m.group(1) != \"CUSUM\":\n    " + anchor, 1)
    open(path, "wb").write(t.encode("utf-8"))
    return path, b


FAULTS = [
    (1, "remove one reconciliation row", f_remove_row,
     ["omitted keys = 0", "reconciliation rows equal"]),
    (2, "duplicate one reconciliation row", f_duplicate_row,
     ["duplicate reconciliation rows = 0"]),
    (3, "add one fake key to the reconciliation", f_fake_key,
     ["extra keys = 0"]),
    (4, "suppress one real key from the pre-change extraction", f_suppress_key,
     ["independently recounted raw entry count", "agree key for key"]),
]


def main():
    clear_pycache()
    state, out, _ = run_guard()
    if state != "GREEN":
        print("BASELINE NOT GREEN:\n" + out[-3000:])
        return 1

    rows = []
    for num, label, mutate, expect in FAULTS:
        path, original = mutate()
        applied = open(path, "rb").read() != original          # re-read from disk
        clear_pycache()
        state, out, failing = run_guard()
        joined = " | ".join(failing).lower()
        reason_ok = any(e.lower() in joined for e in expect)
        open(path, "wb").write(original)
        clear_pycache()
        back, _, _ = run_guard()
        rows.append({
            "fault": num,
            "description": label,
            "target": os.path.relpath(path, ROOT),
            "applied": "YES" if applied else "NO",
            "guard_state": state,
            "intended_reason_matched": "YES" if (state == "RED" and reason_ok) else "NO",
            "guard_failing_checks": " | ".join(failing) if failing else "",
            "restored_state": back,
            "result": "PASS" if (applied and state == "RED" and reason_ok and back == "GREEN") else "FAIL",
        })
        print("fault %d  applied=%s  %s  reason=%s  restored=%s" % (
            num, rows[-1]["applied"], state, rows[-1]["intended_reason_matched"], back))

    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    ok = sum(1 for r in rows if r["result"] == "PASS")
    print("\nrequired 4  applied %d  intended RED %d  restored GREEN %d  crashes %d" % (
        sum(1 for r in rows if r["applied"] == "YES"),
        sum(1 for r in rows if r["intended_reason_matched"] == "YES"),
        sum(1 for r in rows if r["restored_state"] == "GREEN"),
        sum(1 for r in rows if r["guard_state"] == "CRASH")))
    print("RESULT: %d/4 checks passed" % ok)
    return 0 if ok == 4 else 1


if __name__ == "__main__":
    sys.exit(main())
