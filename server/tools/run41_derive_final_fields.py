#!/usr/bin/env python3
"""RUN 41 section 6 - mechanically derive the set of persisted fields that constitute the
final participant judgment.

The owner's prompt names three (final_action, final_confidence, rationale) and instructs that
the real set be derived from the live model rather than guessed from the prompt. Two independent
live authorities are read and cross-checked:

  A. server/app/research_decision.py :: a_researchdecision - the ONLY route that records a final
     response. Every `decision.<attr> = ...` assignment in that function body is, by construction,
     a persisted component of the final response. Read by AST, not by regex.
  B. server/app/research_export.py :: the analysis export column list - the fields that leave the
     instrument as final-decision variables.

A field is SUBSTANTIVE if it is written by the final-response route AND is not the lock timestamp
itself. The lock timestamp is protected separately, because a guard predicated on it that lets it
be cleared is bypassable in two statements.

Writes code_audit/run41_final_judgment_field_derivation.csv and prints the derived set.
"""
from __future__ import annotations
import ast, csv, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
APP = ROOT / "server" / "app"

src = (APP / "research_decision.py").read_text(encoding="utf-8")
tree = ast.parse(src)
fn = next(n for n in ast.walk(tree)
          if isinstance(n, ast.FunctionDef) and n.name == "a_researchdecision")

written: list[str] = []
for node in ast.walk(fn):
    if isinstance(node, ast.Assign):
        for tgt in node.targets:
            if (isinstance(tgt, ast.Attribute) and isinstance(tgt.value, ast.Name)
                    and tgt.value.id == "decision"):
                if tgt.attr not in written:
                    written.append(tgt.attr)

# Authority B: the export's declared final-decision columns.
export_src = (APP / "research_export.py").read_text(encoding="utf-8")
etree = ast.parse(export_src)
# EXPORT_COLUMNS is an annotated assignment (`EXPORT_COLUMNS: tuple[str, ...] = (...)`), so it
# is an ast.AnnAssign and NOT an ast.Assign. Targeting it by name means a rename or a change of
# construct makes this derivation fail loudly instead of silently reporting an empty authority.
export_cols: set[str] = set()
for node in ast.walk(etree):
    tgt = None
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        tgt = node.target.id
    elif isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
        tgt = node.targets[0].id
    if tgt == "EXPORT_COLUMNS" and isinstance(node.value, (ast.List, ast.Tuple)):
        for el in node.value.elts:
            if isinstance(el, ast.Constant) and isinstance(el.value, str):
                export_cols.add(el.value)
if not export_cols:
    raise SystemExit("DERIVATION FAILED: EXPORT_COLUMNS authority read as empty - "
                     "the cross-check would be vacuous, refusing to emit a derivation")

LOCK_STAMP = "final_submitted_at"
PROMPT_NAMED = {"final_action", "final_confidence", "rationale"}

rows = []
for attr in written:
    is_lock = attr == LOCK_STAMP
    rows.append({
        "field": attr,
        "written_by_final_response_route": "yes",
        "appears_in_analysis_export": "yes" if attr in export_cols else "no",
        "role": "final lock timestamp" if is_lock else "substantive final response content",
        "named_in_owner_prompt": "yes" if attr in PROMPT_NAMED else "no",
        "protected_by_trigger": "yes",
        "protection_reason": ("the guard's own precondition - if it can be cleared or moved the "
                              "trigger is bypassable in two statements"
                              if is_lock else
                              "persisted component of the final participant judgment"),
    })

substantive = [r["field"] for r in rows if r["role"] != "final lock timestamp"]
protected = [r["field"] for r in rows]

out = ROOT / "code_audit" / "run41_final_judgment_field_derivation.csv"
with out.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)

print("=" * 78)
print("RUN 41 - mechanically derived final-judgment field set")
print("=" * 78)
for r in rows:
    print(f"  {r['field']:22s} export={r['appears_in_analysis_export']:3s} "
          f"prompt_named={r['named_in_owner_prompt']:3s}  {r['role']}")
print()
print(f"substantive final-response fields ... {len(substantive)}")
print(f"total protected by the trigger ...... {len(protected)}")
print(f"named in the owner's prompt ......... {len(PROMPT_NAMED)}")
extra = sorted(set(substantive) - PROMPT_NAMED)
print(f"DISCREPANCY - substantive fields the prompt did NOT name ({len(extra)}):")
for e in extra:
    print(f"    {e}")
print(f"\nwrote {out.relative_to(ROOT)}")

# Machine-readable for the migration and the guards to consume.
if __name__ == "__main__":
    import json
    print("\nDERIVED_JSON " + json.dumps({"substantive": substantive, "protected": protected}))
