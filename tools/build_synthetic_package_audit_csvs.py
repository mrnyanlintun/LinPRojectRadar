#!/usr/bin/env python3
"""Audit-only. Builds the four synthetic-package audit CSVs under code_audit/."""
import csv, hashlib, os, sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.join(REPO, "research_fixtures/synthetic/OG-SYNTH-0.1")
OUT = os.path.join(REPO, "code_audit")

# ---- 1. file inventory ---------------------------------------------------
inv = []
for pk in ("package_A", "package_B", "package_C"):
    base = os.path.join(ROOT, pk)
    for dp, _, fs in os.walk(base):
        for fn in sorted(fs):
            fp = os.path.join(dp, fn)
            rel = os.path.relpath(fp, base)
            h = hashlib.sha256(open(fp, "rb").read()).hexdigest()
            rows = cols = ""
            if fn.endswith(".csv"):
                with open(fp, newline="", encoding="utf-8") as f:
                    rd = list(csv.reader(f))
                rows = len(rd) - 1
                cols = len(rd[0]) if rd else 0
            inv.append([pk, rel, os.path.getsize(fp), rows, cols, h])
with open(os.path.join(OUT, "synthetic_package_file_inventory.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["archive", "path_within_archive", "bytes", "data_rows", "columns", "sha256"])
    w.writerows(inv)

# ---- 2. checksum results -------------------------------------------------
# All three archives ship the identical programme-level CHECKSUMS.sha256, which
# lists all 90 programme files. Verification is therefore done against a merged
# tree assembled from the three archives.
merged = {}
for pk in ("package_A", "package_B", "package_C"):
    base = os.path.join(ROOT, pk)
    for dp, _, fs in os.walk(base):
        for fn in fs:
            fp = os.path.join(dp, fn)
            merged.setdefault(os.path.relpath(fp, base).replace(os.sep, "/"), fp)
res = []
for line in open(os.path.join(ROOT, "package_A/CHECKSUMS.sha256"), encoding="utf-8"):
    line = line.strip()
    if not line:
        continue
    exp, path = line.split(None, 1)
    fp = merged.get(path)
    if fp is None:
        res.append([path, exp, "", "MISSING", "not supplied with the three package archives"])
        continue
    got = hashlib.sha256(open(fp, "rb").read()).hexdigest()
    res.append([path, exp, got, "MATCH" if got == exp else "MISMATCH", ""])
with open(os.path.join(OUT, "synthetic_package_checksum_results.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["path_in_checksum_file", "expected_sha256", "computed_sha256", "result", "note"])
    w.writerows(res)
print("checksums:", sum(1 for r in res if r[3] == "MATCH"), "match,",
      sum(1 for r in res if r[3] == "MISMATCH"), "mismatch,",
      sum(1 for r in res if r[3] == "MISSING"), "missing, of", len(res))
print("inventory:", len(inv), "files")
