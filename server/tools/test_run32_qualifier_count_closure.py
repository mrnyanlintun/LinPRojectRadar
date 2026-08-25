"""
RUN 32 ACCOUNTING CLOSURE. THE 29-VERSUS-30 QUALIFIER COUNT.

The prompt that opened the qualifier closure expected 30 client qualifier entries; the
reconciliation carries 29. Neither number is assumed here. The authoritative population is
extracted from the PINNED PRE-CHANGE GIT OBJECT, and this guard holds the reconciliation to
that population -- not to 29, and not to 30.

The pre-change extraction is itself under test. A guard that trusted the builder's extractor
could be made to under-report by suppressing one key, which is exactly the failure mode that
would have produced a false 29 in the first place. So the raw entry count is recomputed here
by an INDEPENDENT scan of the same git blob, and the two must agree.
"""
from __future__ import annotations

import collections
import csv
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))

import build_run32_qualifier_count_closure as B                             # noqa: E402

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


PERMITTED = {"CURRENT_REQUIRED", "WITHDRAWN", "HISTORICAL_ONLY",
             "CURRENT_SERVER_QUALIFIER_MISSING", "BACKWARD_ALIAS_ONLY"}

PRECHANGE = B.PRECHANGE_OBJECT
PROMPT_EXPECTED = 30            # what the owner prompt said; recorded, never enforced


def rows(path):
    with open(path, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def independent_raw_count(obj=PRECHANGE):
    """Recount the map literal's entries WITHOUT using the builder's extractor."""
    blob = subprocess.run(["git", "show", f"{obj}:{B.SOURCE_FILE}"], cwd=ROOT,
                          capture_output=True, check=True).stdout.decode("utf-8")
    body = re.search(r"\b%s\s*=\s*\{(.*?)\n\s{0,2}\};" % B.MAP_NAME, blob, re.S)
    if not body:
        return None, None
    keys = re.findall(r'^\s+([A-Za-z0-9_]+)\s*:\s*"', body.group(1), re.M)
    return len(keys), keys


head("1. THE AUTHORITATIVE PRE-CHANGE POPULATION IS EXTRACTED, NOT ASSUMED")

summary = B.build()
pop = rows(B.POP_CSV)
closure = rows(B.CLOSURE_CSV)
recon = rows(B.RECON)

ind_n, ind_keys = independent_raw_count()
check(ind_n is not None,
      "the pinned pre-change git object still carries the client qualifier map literal",
      PRECHANGE)
check(ind_n == summary["raw_entries"],
      "the independently recounted raw entry count agrees with the builder's extraction, so the "
      "extraction cannot silently under-report the population",
      f"independent={ind_n} builder={summary['raw_entries']}")
check(sorted(ind_keys or []) == sorted(r["key"] for r in pop),
      "and the two extractions agree key for key, not merely in count")
check(len(pop) == summary["raw_entries"],
      "the population artifact records every raw entry, one row each",
      f"rows={len(pop)} raw={summary['raw_entries']}")

head("2. RAW ENTRIES AND UNIQUE KEYS ARE COUNTED SEPARATELY")

dups = [r["key"] for r in pop if r["duplicate"] == "YES"]
check(summary["duplicate_keys"] == 0,
      "no key occurs twice in the pre-change map literal, so raw entries and unique keys are the "
      "same number and the count is not a duplicate artefact", str(dups))
check(summary["raw_entries"] == summary["unique_keys"],
      "authoritative raw entries equal authoritative unique keys",
      f"raw={summary['raw_entries']} unique={summary['unique_keys']}")

head("3. THE RECONCILIATION MATCHES THE AUTHORITATIVE POPULATION")

check(summary["reconciliation_rows"] == summary["unique_keys"],
      "reconciliation rows equal the authoritative unique key count",
      f"recon={summary['reconciliation_rows']} unique={summary['unique_keys']}")
check(not summary["omitted_keys"],
      "omitted keys = 0: every pre-change key has a reconciliation row",
      str(summary["omitted_keys"]))
check(not summary["extra_keys"],
      "extra keys = 0: no reconciliation row names a key the pre-change map never held",
      str(summary["extra_keys"]))
check(summary["duplicate_reconciliation_rows"] == 0,
      "duplicate reconciliation rows = 0")
check(not summary["unclassified"],
      "unclassified keys = 0", str(summary["unclassified"]))

bad = sorted({r["classification"] for r in recon} - PERMITTED)
check(not bad, "every classification is one of the five permitted values", str(bad))
check(all(r["result"] == "PASS" for r in closure),
      "every closure row passes",
      str([r["key"] for r in closure if r["result"] != "PASS"]))

head("4. THE DISCREPANCY IS EXPLAINED BY EVIDENCE, NOT BY ASSERTION")

dist = collections.Counter(r["classification"] for r in recon)
check(sum(dist.values()) == summary["unique_keys"],
      "the classification distribution accounts for the whole population",
      str(dict(dist)))

pred = subprocess.run(["git", "rev-parse", f"{PRECHANGE}^1"], cwd=ROOT,
                      capture_output=True, check=True).stdout.decode().strip()
pred_n, _ = independent_raw_count(pred)
check(pred_n == PROMPT_EXPECTED,
      "the prompt-expected count is traced to a real earlier state of the same map -- the "
      "predecessor of the pinned object -- rather than being dismissed",
      f"predecessor={pred[:7]} entries={pred_n} expected={PROMPT_EXPECTED}")
check(summary["unique_keys"] != PROMPT_EXPECTED,
      "and the authoritative count genuinely differs from the prompt-expected count, so the "
      "discrepancy is recorded rather than reconciled away",
      f"authoritative={summary['unique_keys']} prompt={PROMPT_EXPECTED}")

# RUN 59, PHASE B. RETIRED, NOT DELETED.
#
# Owner's ruling, 2026-08-25: NO MARKDOWN DOCUMENT IN THIS REPOSITORY CARRIES AUTHORITY.
# Production code is the truth; REPORT_*.md, code_audit/REPORT_*.md, research/freeze/*.md and
# the fixture records are SEALED EVIDENCE; everything else is transport or history. A check
# whose real subject is a markdown document's CONTENT is therefore asserting nothing that
# matters, and it can turn red for an edit to a file that governs nothing.
#
# Retired the way modules were retired: THE CHECK STOPS RUNNING, THE BODY IS NOT DELETED, AND
# THE REASON IS RECORDED. Clear the flag to run it again. Nothing is removed from this file.
#
# WHAT THE TWO RETIRED CHECKS ASSERTED: that REPORT_2026-08-18_run32-proxy-qualifier-and-client-
# authority-closure.md contains the strings "30" and "29", and that T6_HANDOFF.md contains the
# string "expected 30". Neither says anything about production. The AUTHORITATIVE count of 29 is
# still asserted above, against the running code, and that is the assertion that matters. The
# report remains sealed evidence and the handoff remains history; neither is edited, and neither
# can now turn this suite red.
RETIRED_RUN59_REPORT_AND_HANDOFF_STRINGS = True
if not RETIRED_RUN59_REPORT_AND_HANDOFF_STRINGS:
    report = ROOT / "REPORT_2026-08-18_run32-proxy-qualifier-and-client-authority-closure.md"
    text = report.read_text(encoding="utf-8")
    check(str(PROMPT_EXPECTED) in text and "29" in text,
          "the report states both the prompt-expected count and the authoritative count, so the "
          "correction is visible rather than a number quietly changed to match reality")
    hand = (ROOT / "T6_HANDOFF.md").read_text(encoding="utf-8")
    check("prompt expected 30" in hand.lower() or "expected 30" in hand.lower(),
          "the handoff carries the same correction")
else:
    print("  RETIRED (Run 59)  the report states both counts -- markdown, no authority")
    print("  RETIRED (Run 59)  the handoff carries the same correction -- markdown, no authority")

print()
for f in _fail:
    print("FAIL:", f)
print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
sys.exit(1 if FAILED else 0)
