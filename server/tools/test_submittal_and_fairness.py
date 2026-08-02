#!/usr/bin/env python3
"""
The fairness gate is removed, and Submittal is split into the register form.

Run (from server/):

    PYTHONIOENCODING=utf-8 python tools/test_submittal_and_fairness.py

No database, no server, no network. Pure functions and a source scan.

WHY A SOURCE SCAN AS WELL AS A BEHAVIOURAL CHECK. The gate could never fire, so a purely
behavioural check "does fairness_gate come back False" passed BEFORE the change too, and would
have gone on passing if the dead branch had been left in place. It is not evidence that the gate
was removed. The behavioural check pins the contract; the source scan pins the removal. Both are
needed and both are proven able to fail.

THE SCAN MATCHES CODE, NOT PROSE. A previous session wrote a check that searched for an
expression which also appeared in the comment explaining it, so deleting the real code left the
check green. Every scan below strips comment lines first.
"""
from __future__ import annotations

import ast
import io
import pathlib
import sys
import tokenize

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app.extraction_fields import (  # noqa: E402
    DOC_TYPES, LEGACY_TYPE_ALIASES, canonical_doc_type, extraction_fields_for, is_mapped,
)
from app.extraction_merge import (  # noqa: E402
    DOC_RISK_DOC_TYPES, SIGNAL_INPUT_KEYS, assemble_signal_inputs, assembly_report,
)
from app.simulation.models_decision import run_abm_governance  # noqa: E402

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


def _docstring_lines(tree: ast.AST) -> set[int]:
    """Every line occupied by a module, class or function docstring."""
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef,
                                 ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if not body:
            continue
        first = body[0]
        if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)):
            lines.update(range(first.lineno, (first.end_lineno or first.lineno) + 1))
    return lines


def code_of(module_path: str) -> str:
    """
    Executable source only: comments and docstrings removed, string LITERALS kept.

    TOKENIZED, NOT LINE-SCANNED, AND THAT MATTERS. The first version of this helper tracked
    triple-quote toggling by hand. It desynchronised on the first docstring containing a quote
    form it did not expect and silently discarded 735 of extraction_merge.py's 964 lines, 76% of
    the file, including every merge branch. Every scan built on it was therefore near-vacuous:
    fault injection wrote `acc.set_field("fairnessSensitive", True)` into the pay_application
    branch and the suite stayed green, because that branch was not in the text being searched.

    String literals are deliberately KEPT, because a merge branch writing a field names it as a
    literal and that is exactly what these scans look for. Only prose is removed.
    """
    raw = io.open(pathlib.Path(__file__).resolve().parents[1] / module_path,
                  encoding="utf-8").read()
    drop = _docstring_lines(ast.parse(raw))
    kept: list[str] = []
    for tok in tokenize.generate_tokens(io.StringIO(raw).readline):
        if tok.type == tokenize.COMMENT:
            continue
        if tok.type == tokenize.STRING and tok.start[0] in drop:
            continue
        if tok.string.strip():
            kept.append(tok.string)
    return " ".join(kept)


ESCALATING = {
    "signals": {
        "evm": {"status": "red"},
        "mc": {"status": "red"},
        "cusum": {"status": "red", "breached": True},
        "doc": {"status": "red"},
    }
}

print("=" * 78)
print("GUARANTEE 1: the fairness gate is gone from the code, not merely unreachable")
print("=" * 78)

# The precondition. If this ever becomes False the gate would start firing and everything below
# is the wrong question, so it is asserted rather than assumed.
check("fairnessSensitive" not in SIGNAL_INPUT_KEYS,
      "fairnessSensitive is not a signalInput the merge can produce",
      f"{len(SIGNAL_INPUT_KEYS)} keys")
merge_src = code_of("app/extraction_merge.py")
check("fairnessSensitive" not in merge_src,
      "and no merge branch writes it (comments stripped before matching)")

decision_src = code_of("app/simulation/models_decision.py")
check("fairnessSensitive" not in decision_src,
      "models_decision no longer reads fairnessSensitive (comments stripped)")
check("fairness gate" not in decision_src,
      "and the fairness-gated escalation wording is gone")

# Behaviour. si carries the key set to True AND the project escalates: the exact input the old
# gate required. It must still come back False, because the gate does not exist.
gated = dict(ESCALATING)
gated["fairnessSensitive"] = True


def governance(si: dict) -> dict:
    """
    Never raises. A module that explodes must produce a RED CHECK, not a dead suite.

    Fault injection proved this necessary: renaming the output key made run_abm_governance raise
    KeyError, this file died at import-time module scope, and it printed NO `RESULT:` line at all,
    which reads exactly like a clean run.
    """
    try:
        return run_abm_governance(si, lambda: 0.5, "2026-07-31") or {}
    except Exception as exc:  # noqa: BLE001 - the point is that nothing escapes
        print(f"        (run_abm_governance raised {type(exc).__name__}: {exc})")
        return {}


out = governance(gated)
check(out.get("state") in ("Red", "Red-review"),
      "the fixture does escalate, so the old gate's other condition is met", str(out.get("state")))
check(out.get("fairness_gate") is False,
      "fairness_gate is False even with fairnessSensitive True and an escalation",
      str(out.get("fairness_gate")))
check("fairness_gate" in out,
      "and the key is still present, because assets/js/app.js reads it")
check(out.get("authority") == "Program director / PMO lead",
      "escalation names one authority, not a fairness variant", str(out.get("authority")))
check(out.get("action") == "Recovery-plan review and management escalation",
      "and one escalation action", str(out.get("action")))

print()
print("=" * 78)
print("GUARANTEE 2: Submittal is the register form, and the retired name still merges")
print("=" * 78)

check(canonical_doc_type("submittal") == "submittal_register",
      "the retired type canonicalises to the register", canonical_doc_type("submittal"))
check(LEGACY_TYPE_ALIASES.get("submittal") == "submittal_register",
      "the alias is declared, not incidental")
check("submittal_register" in DOC_TYPES,
      "the register is the type the classifier is offered")
check("submittal" not in DOC_TYPES,
      "and the ambiguous name is no longer offered")
check(canonical_doc_type("rfi") == "rfi",
      "canonicalisation is identity for everything else")

check(extraction_fields_for("submittal") == extraction_fields_for("submittal_register"),
      "the retired name resolves to the register's field list",
      str(extraction_fields_for("submittal")))
check("submittals_total" in extraction_fields_for("submittal_register"),
      "which is register-shaped: totals, not one item's state")

check("submittal_register" in DOC_RISK_DOC_TYPES,
      "the register still carries a document risk score")

# is_mapped IS ASKED ABOUT STORED STRINGS, not only canonical ones. documents.py:721 calls it
# with `doc.doc_type` straight off the row, and documents.py:825 puts the answer in the upload
# response as `contributes`. A stored `submittal` failing here would tell the PM their document
# contributed nothing, while the merge quietly used it. Fault injection caught this check
# missing: removing the alias resolution from is_mapped left the suite green, because the merge
# fold canonicalises before it asks.
check(is_mapped("submittal") is True,
      "a row stored under the retired name is still reported as contributing")
check(is_mapped("not_a_real_type") is False,
      "and an unknown type still is not", str(is_mapped("not_a_real_type")))

# THE ANTI-SILENT-LOSS PROPERTY. Document rows already store the retired string. If the rename
# had been made without the alias they would stop contributing at the next recompute, with no
# error anywhere: exactly the silent loss this codebase refuses.
EX = {"document_risk_score": 0.4, "document_date": "2026-06-30",
      "submittals_total": 40, "submittals_rejected": 6}


def one(doc_type: str) -> dict:
    return assemble_signal_inputs(
        [{"sha256": "a" * 64, "doc_type": doc_type, "extraction": EX, "filename": "s.pdf"}])


legacy, current = one("submittal"), one("submittal_register")
check(legacy.get("submittalsTotal") == 40 and legacy.get("submittalsRejected") == 6,
      "a row stored under the retired name still contributes its figures",
      f"{legacy.get('submittalsTotal')}/{legacy.get('submittalsRejected')}")
check(legacy == current,
      "and produces byte-identical signalInputs to the current name")
check(legacy.get("docRiskScore") == 0.4,
      "including the document risk score", str(legacy.get("docRiskScore")))

rep = assembly_report(
    [{"sha256": "a" * 64, "doc_type": "submittal", "extraction": EX, "filename": "s.pdf"}])
check(not rep.get("unmapped"),
      "and the assembly report does not call it unmapped", str(rep.get("unmapped"))[:80])

print()
print("=" * 78)
failed = [r for r in results if not r[0]]
print(f"RESULT: {len(results) - len(failed)}/{len(results)} checks passed")
for _, label, detail in failed:
    print(f"  FAILED: {label}  {detail}")
print("=" * 78)
sys.exit(1 if failed else 0)
