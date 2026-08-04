#!/usr/bin/env python3
"""
The extraction prompt's anti-substitution contract, and the milestones_json shape hint.

Run (from server/):

    PYTHONIOENCODING=utf-8 python tools/test_extraction_prompt.py

WHY THIS SUITE EXISTS AND WHAT IT CANNOT PROVE

`build_prompt` had no suite at all before 2026-08-05. The prompt is the contract, and until now
nothing asserted its text survives an edit. This suite is DETERMINISTIC and needs neither
`ANTHROPIC_API_KEY` nor a real document — it asserts the prompt's own wording, not what a model
does with it, so it can run in every environment and CI.

It CANNOT prove the fix works. It can only prove the words are still there. The actual proof — a
real model, given this prompt, no longer substituting a reporting period for a project baseline
date, and now returning the activity table it was previously missing — is two real calls against
two real project documents, recorded in `REPORT_2026-08-05_extraction-substitution.md`. That
report is the evidence; this suite is the tripwire that catches someone editing the words away
without re-running the real check. See `tools/real_extraction_regression.py` for the (optional,
key-and-documents-gated) live re-verification script, which is NOT named `test_*` on purpose —
see that file's own docstring for why it must never be swept into the standard suite run.

THE DEFECT THIS GUARDS AGAINST HAD NO GUARD AT ALL

`project_start_date` / `project_end_date` came back as well-formed, in-range dates — a reporting
period the model found nearby and mislabelled. Neither `validate_doc_risk_score` nor
`validate_numeric_fields` could have caught it: both guard VALUE, and a substituted date is a
perfectly good date. The only place this can be caught is the prompt itself, which is why the
words matter enough to pin.
"""
from __future__ import annotations

import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

RESULTS: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    RESULTS.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))


def finish() -> None:
    failed = [r for r in RESULTS if not r[0]]
    print(f"\nRESULT: {len(RESULTS) - len(failed)}/{len(RESULTS)} checks passed")
    sys.exit(1 if failed else 0)


def section(title: str) -> None:
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78)


def main() -> None:
    from app.extraction_client import build_prompt
    from app.extraction_fields import DOC_TYPES, extraction_fields_for

    section("1. THE ANTI-SUBSTITUTION PARAGRAPH IS PRESENT, FOR EVERY DOCUMENT TYPE")

    # A phrase from each of the three load-bearing sentences, so a partial edit (one sentence
    # kept, the load-bearing clause dropped) is still caught rather than passing on the survival
    # of a neighbouring word.
    REQUIRED_PHRASES = [
        "under a label or heading whose meaning matches the field's name",
        "never a substitute",
        "point to the specific label in the document",
    ]
    # The three named examples from the real defect, so a rewrite that drops the CONCRETE cases
    # (and keeps only the abstract rule) is caught too — the abstract rule alone did not stop the
    # original defect; a model needs the concrete shape of "a value under no matching label".
    NAMED_EXAMPLES = [
        "a reporting period is not a project start or end date",
        "an issue date or a data date is not a baseline date",
    ]
    for doc_type in DOC_TYPES:
        fields = extraction_fields_for(doc_type)
        prompt = build_prompt(doc_type, fields)
        for phrase in REQUIRED_PHRASES:
            check(phrase in prompt, f"{doc_type}: prompt carries {phrase[:40]!r}")
    # Examples checked once, not per doc type — they are the same sentence regardless of type.
    one_prompt = build_prompt("contract_value", extraction_fields_for("contract_value"))
    for phrase in NAMED_EXAMPLES:
        check(phrase in one_prompt, f"named example present: {phrase[:50]!r}")

    section("2. milestones_json's SHAPE HINT: PRESENT ONLY WHEN THE FIELD IS REQUESTED")

    HINT_MARKER = "one object per row of that table"

    with_it = [t for t in DOC_TYPES if "milestones_json" in extraction_fields_for(t)]
    without_it = [t for t in DOC_TYPES if "milestones_json" not in extraction_fields_for(t)]
    check(bool(with_it) and bool(without_it),
          "the vocabulary genuinely has both cases to test",
          f"with={with_it} without-sample={without_it[:2]}")

    for doc_type in with_it:
        fields = extraction_fields_for(doc_type)
        prompt = build_prompt(doc_type, fields)
        check(HINT_MARKER in prompt,
              f"{doc_type}: milestones_json is requested, so the shape hint IS present")

    for doc_type in without_it:
        fields = extraction_fields_for(doc_type)
        prompt = build_prompt(doc_type, fields)
        check(HINT_MARKER not in prompt,
              f"{doc_type}: milestones_json is NOT requested, so the hint is ABSENT",
              "would silently grow every prompt if this leaked")

    section("3. THE HINT SAYS DATES INSIDE THE TABLE ARE NOT ISO-CONSTRAINED")

    # The real activity table carries THREE non-ISO date shapes in one column
    # ('12-Jan-26', '29-May', '14 August 2026', and a fourth with a trailing actual-marker,
    # '24-Mar-26 A' — a scheduling tool's own convention). The top-level "Dates as YYYY-MM-DD"
    # instruction, if it applied inside the table too, would tell the model to silently
    # reformat or drop the actual-marker suffix. This check is what stops a future edit from
    # removing the carve-out and reintroducing that.
    su_prompt = build_prompt("schedule_update", extraction_fields_for("schedule_update"))
    check("NOT required to be YYYY-MM-DD" in su_prompt,
          "the table-dates-are-not-ISO carve-out is present in the hint")

    section("4. PRE-EXISTING INVARIANTS THIS CHANGE MUST NOT HAVE DISTURBED")

    dr_prompt = build_prompt("submittal_register", extraction_fields_for("submittal_register"))
    check("between 0 and 1 inclusive" in dr_prompt,
          "document_risk_score's 0..1 band clause survives the rewrite")
    check("never a count and never a percentage" in dr_prompt,
          "and its scale warning survives")
    every_prompt_all_types = [build_prompt(t, extraction_fields_for(t)) for t in DOC_TYPES]
    check(all("Do not compute indices" in p for p in every_prompt_all_types),
          "'Do not compute indices' still present in every document type's prompt")
    check(all("Dates as YYYY-MM-DD" in p for p in every_prompt_all_types),
          "the top-level ISO date instruction still present in every prompt")
    check(all(p.rstrip().endswith("Return JSON only, no markdown, no commentary.")
             for p in every_prompt_all_types),
          "every prompt still ends with the output-format instruction")

    section("5. THE FIELD LIST ITSELF IS STILL QUOTED VERBATIM INTO THE PROMPT")

    import json as _json
    for doc_type in ("pay_application", "schedule_update"):
        fields = extraction_fields_for(doc_type)
        prompt = build_prompt(doc_type, fields)
        check(_json.dumps(fields) in prompt,
              f"{doc_type}: the exact field list JSON appears in its prompt",
              str(fields))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — a crash must print a FAILING result line
        import traceback
        traceback.print_exc()
        check(False, f"suite crashed: {type(exc).__name__}: {exc}")
    finish()
