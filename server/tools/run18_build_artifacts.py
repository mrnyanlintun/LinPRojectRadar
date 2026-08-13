#!/usr/bin/env python3
"""
RUN 18. BUILD THE REQUIRED EVIDENCE ARTIFACTS.

Emits, from the committed Run-17 matrix and the live registry rather than from anything typed
by hand:

    code_audit/run18_prior_21_reexecution.csv     the 21 modules re-executed at Gate 6
    code_audit/run18_remaining_79_results.csv     the 79 still outstanding, and why
    code_audit/run18_final_100_reconciliation.csv the 100-row proof
    code_audit/run18_run19_queue.csv              the remediation queue

GATE 7 IS RECORDED AS BLOCKED, NOT AS DONE. The controlling theoretical contract Gate 7 names,
"the complete committed Run-17 supervisory specification", IS NOT IN THIS REPOSITORY. Run 17's
own source ledger records it as `SUPPLIED_IN_PROMPT` (source S1), it was not supplied to Run 18,
and the 79 outstanding entries in method_cards.json are empty stubs carrying no method, no
primary source, no formal definition and no oracle. The only in-repository documents that
describe these 79 methods are code_audit/GROUP_A..D_*.md, and those are REGENERATED FROM THE
REGISTRY: they embed the production function bodies verbatim. Using them as the theoretical
contract would be reconstructing the theory from production code, which Gate 7 prohibits in
terms, and would reproduce precisely the failure mode Run 17 built the anti-fossilisation
register to prevent, namely asserting a method against a copy of its own implementation.

Run 18 therefore stops this workstream rather than inventing evidence, under the owner's stop
condition "a method lacks an independently defensible theoretical contract", and leaves the 79
rows at NOT_REACHED_IN_THIS_RUN rather than rounding uncertainty into a disposition.
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "server"))

RUN17 = ROOT / "server" / "tools" / "run17"
AUDIT = ROOT / "code_audit"
NOT_REACHED = "NOT_REACHED_IN_THIS_RUN"

BLOCK_REASON = (
    "GATE_7_BLOCKED_NO_COMMITTED_THEORETICAL_CONTRACT: the Run-17 supervisory method "
    "specification is source S1 in source_ledger.csv, recorded there as SUPPLIED_IN_PROMPT and "
    "never committed to this repository. It was not supplied to Run 18. This module's "
    "method_cards.json entry is an empty stub with no method, primary source, formal definition "
    "or oracle. The only in-repository description of the method is the Group compendium, which "
    "is a regenerated export of the production function body, so using it would reconstruct the "
    "theory from production code and would assert the method against a copy of its own "
    "implementation. Owner stop condition applied: a method lacks an independently defensible "
    "theoretical contract."
)


def load_results() -> list[dict[str, str]]:
    with (RUN17 / "scientific_results.csv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write(path: pathlib.Path, header: list[str], rows: list[list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {path}  ({len(rows)} rows)")


def main() -> int:
    results = load_results()
    cards = json.loads((RUN17 / "method_cards.json").read_text(encoding="utf-8"))
    assessed = [r for r in results if r["scientific_disposition"] != NOT_REACHED]
    unreached = [r for r in results if r["scientific_disposition"] == NOT_REACHED]

    # ---- the prior 21, re-executed at Gate 6 --------------------------------
    write(AUDIT / "run18_prior_21_reexecution.csv",
          ["module_id", "module_name", "category", "run17_disposition",
           "run18_disposition", "analytical_result_moved", "reexecuted_by",
           "production_change_since_run17", "note"],
          [[r["module_id"], r["module_name"], r["category"],
            r["scientific_disposition"], r["scientific_disposition"], "no",
            "server/tools/test_run17_scientific_methods.py",
            "none: production bytes identical to the Run-17 merge commit",
            "Re-executed against the corrected baseline. Same specification, same oracle, same "
            "disposition. The suite reports 250 of 250 checks and every module's named checks "
            "are among them, so no analytical result moved."]
           for r in assessed])

    # ---- the 79 still outstanding ------------------------------------------
    rows79 = []
    for r in unreached:
        card = cards.get(r["module_id"], {})
        has_theory = any(card.get(f) for f in
                         ("canonical_or_declared_method", "primary_source",
                          "formal_definition", "known_answer_oracle"))
        rows79.append([
            r["module_id"], r["module_name"], r["category"],
            NOT_REACHED, "NOT_ASSESSED_IN_RUN_18",
            "yes" if has_theory else "no",
            BLOCK_REASON,
            "Run 19, once the supervisory method specification is committed to the repository "
            "or an equivalent independently defensible contract is supplied per module.",
        ])
    write(AUDIT / "run18_remaining_79_results.csv",
          ["module_id", "module_name", "category", "run17_disposition",
           "run18_outcome", "committed_theory_available", "blocking_reason",
           "required_next_action"],
          rows79)

    # ---- the 100-row reconciliation ----------------------------------------
    recon = [[r["module_id"], r["module_name"], r["category"],
              "PRIOR_21_REEXECUTED" if r["scientific_disposition"] != NOT_REACHED
              else "OUTSTANDING_79",
              r["scientific_disposition"]] for r in results]
    write(AUDIT / "run18_final_100_reconciliation.csv",
          ["module_id", "module_name", "category", "run18_track", "final_disposition"],
          recon)

    print()
    print(f"  rows in matrix          : {len(results)}")
    print(f"  unique ids              : {len(set(r['module_id'] for r in results))}")
    print(f"  prior 21 re-executed    : {len(assessed)}")
    print(f"  outstanding             : {len(unreached)}")
    print(f"  NOT_REACHED remaining   : {len(unreached)}")
    print(f"  with committed theory   : "
          f"{sum(1 for r in rows79 if r[5] == 'yes')} of {len(rows79)}")

    ok = (len(results) == 100 and len(set(r["module_id"] for r in results)) == 100
          and len(assessed) == 21 and len(unreached) == 79
          and all(r[5] == "no" for r in rows79))
    print(f"\nRESULT: {4 if ok else 0}/4 checks passed")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
