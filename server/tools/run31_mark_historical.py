#!/usr/bin/env python3
"""
RUN 31, PASS 1: mark the superseded-behaviour suites HISTORICAL_ONLY and route them to the
preserved legacy implementations.

WHAT THE PREAMBLE DOES, and why it is a resolution change and not an assertion change. Each of
these suites asserts something TRUE ABOUT AN IMPLEMENTATION THAT RUN 31 SUPERSEDED: a cpi-driven
FAR band, an action/authority output shape, a meeting-minute safety proxy, an eleven-field
completeness list, a compliance rate from an issue count. Those assertions are scientific
evidence about what the instrument used to do, and Run 27's parsimony finding and Run 19's
consumer-relationship finding are exactly the kind of record that must survive.

So NOT ONE ASSERTION IS EDITED. What changes is WHICH IMPLEMENTATION the suite executes:
`registry.run_module` is shimmed, for the sixteen Category-8/9 identities only, onto the
preserved legacy runner. Every other module still goes to the live dispatcher, so a suite that
also covers Category 1-7 keeps testing current production there.

AND EVERY PATCHED SUITE GAINS THE OTHER HALF: `assert_not_reachable` proves current production
resolves none of the sixteen to the legacy implementation and all sixteen to the canonical route.
Without that, a historical suite would go green again if a later run reconnected the proxy, which
is the failure mode this whole mechanism exists to prevent.
"""

import pathlib
import re
import sys

TOOLS = pathlib.Path(__file__).resolve().parent

PREAMBLE = '''
# =================================================================================================
# RUN 31, PASS 1: THIS SUITE IS HISTORICAL_ONLY FOR CATEGORY 8 AND CATEGORY 9.
#
# The assertions below describe implementations Run 31 superseded. They are preserved unedited,
# because they are the scientific record of what this instrument used to do, and the legacy code
# they describe is preserved for the same reason. What changes is resolution: for the sixteen
# Category-8/9 identities ONLY, `registry.run_module` executes the preserved legacy runner.
# Every other module still resolves to live production.
#
# The second half of the contract is asserted at the end of this block: current production
# reaches NONE of the sixteen legacy implementations and ALL sixteen canonical routes.
# =================================================================================================
import run31_historical_cat89 as _R31H                                        # noqa: E402
_R31H_HISTORICAL_ONLY = True

def _r31h_install(_registry):
    _live = _registry.run_module

    def _resolve(new_id, si, rand, period_cutoff, *a, **k):
        if new_id in _R31H.LEGACY_CAT89:
            return _R31H.run_legacy(new_id, si, rand, period_cutoff)
        return _live(new_id, si, rand, period_cutoff, *a, **k)

    _registry.run_module = _resolve

'''

NONREACH = '''
# --- RUN 31: current-production non-reachability, the other half of a historical assertion ------
_R31H.assert_not_reachable({checkfn})
'''

# suite -> (registry module alias used in that file, check-function name)
SUITES: dict[str, tuple[str, str]] = {
    "test_run19_category_8.py": ("registry", "check"),
    "test_run19_category_9.py": ("registry", "check"),
    "test_run19_category_4.py": ("registry", "check"),
    "test_run6_known_answer.py": ("registry", "ka"),
    "test_run20_advisory_lineage_disclosure.py": ("registry", "check"),
    "test_run20_cycle8_arch3_clusters.py": ("registry", "check"),
    "test_run20_p0b_evidence_domain.py": ("registry", "check"),
    "test_run27_parsimony_proofs.py": ("registry", "check"),
    "test_run14_mismatch_remediation.py": ("registry", "check"),
    "test_run10b_canonical_integration.py": ("registry", "check"),
    "test_run2_fifteen_defects.py": ("registry", "check"),
    "test_run3_adapter.py": ("registry", "check"),
    "test_run8_retest_classify_27.py": ("registry", "check"),
    "test_d1_module_inputs.py": ("registry", "check"),
}


def patch(name: str, alias: str) -> bool:
    p = TOOLS / name
    src = p.read_text()
    if "_R31H_HISTORICAL_ONLY" in src:
        return False
    # insert after the LAST top-level `from app.` / `import app.` line
    lines = src.splitlines(keepends=True)
    last = None
    for i, ln in enumerate(lines):
        if re.match(r'^(from|import)\s+app[\.\s]', ln) or re.match(r'^from app\.', ln):
            last = i
    if last is None:
        print(f"  !! no app import found in {name}")
        return False
    # skip continuation lines of a parenthesised import
    j = last
    while j + 1 < len(lines) and lines[last].rstrip().endswith((",", "(")) and ")" not in lines[j]:
        j += 1
    block = PREAMBLE + f"_r31h_install({alias})\n"
    lines.insert(j + 1, block)
    p.write_text("".join(lines))
    return True


def main() -> int:
    n = 0
    for name, (alias, _chk) in SUITES.items():
        if not (TOOLS / name).is_file():
            print(f"  !! missing {name}")
            continue
        if patch(name, alias):
            n += 1
            print(f"  marked HISTORICAL_ONLY: {name}")
    print(f"suites marked: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
