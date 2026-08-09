#!/usr/bin/env python3
"""
Four document rows that can never light up: the fix and the sweep.

Run (from server/):

    PYTHONIOENCODING=utf-8 python tools/test_document_rows.py

No database, no model key, no live document required — every check here is either a static
string-key sweep against the current DOC_TYPES vocabulary, or a deterministic pin of the
classifier prompt's own wording. It CANNOT prove the classifier now recognises a design-query
titled RFI log or tells a Schedule of Values from a Pay Application on a real document — that
needs a real model call against a real file, which this environment has neither. It proves the
words the classifier will read are the ones intended, and that no diagram or client surface keys
on a document-type string the server no longer produces.

GUARANTEE 1 IS WRITTEN TO FAIL. Every detector below is run against a deliberately-planted bad
string BEFORE it is trusted against the real files, so a detector with a clause that can never be
false (the exact failure mode a prior phase of this codebase shipped) is caught here rather than
six months from now.
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

ROOT = pathlib.Path(__file__).resolve().parents[2]

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


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


# --------------------------------------------------------------------- retired-key detector
#
# A key is "retired" if it is the bare individual-RFI or bare-submittal string, quoted, as a
# dict/array KEY or a plain array entry — not a substring of a longer, current name like
# 'rfi_log' or 'submittal_register'. Word-boundary-anchored on the quote so 'rfi_log' and
# 'rfa_log' are never flagged.
RETIRED_KEY_RE = re.compile(r"""(['"])(rfi|submittal)\1""")


def find_retired_keys(text: str) -> list[str]:
    return [m.group(0) for m in RETIRED_KEY_RE.finditer(text)]


def main() -> None:
    from app.extraction_fields import CLASSIFY_HINTS, DOC_TYPES, UI_ONLY_DOC_TYPES

    section("0. SELF-TEST: THE RETIRED-KEY DETECTOR CAN ACTUALLY FAIL")

    planted_bad = "var DOC_KEYS = ['contract_value', 'rfi', 'submittal', 'rfi_log'];"
    planted_clean = "var DOC_KEYS = ['contract_value', 'rfi_log', 'rfa_log', 'submittal_register'];"
    check(find_retired_keys(planted_bad) == ["'rfi'", "'submittal'"],
          "detector flags a planted bare 'rfi' and bare 'submittal'",
          str(find_retired_keys(planted_bad)))
    check(find_retired_keys(planted_clean) == [],
          "detector does NOT flag 'rfi_log' / 'rfa_log' / 'submittal_register' "
          "(no false positive on the current, correct keys)",
          str(find_retired_keys(planted_clean)))

    section("1. THE STRING-KEY SWEEP: NO SURFACE KEYS ON A RETIRED DOC-TYPE STRING")

    SWEPT_FILES = [
        "assets/js/neural_flow.js",
        "assets/js/signals.js",
        "assets/js/simulations.js",
    ]
    for rel in SWEPT_FILES:
        found = find_retired_keys(read(rel))
        check(not found, f"{rel}: no retired 'rfi' / 'submittal' key", str(found))

    section("1b. app.js's cat9 COMPARISON (the fourth instance of the class)")

    app_js = read("assets/js/app.js")
    check('cat.id === "cat9"' not in app_js,
          "app.js no longer compares cat.id against the retired 'cat9' scheme")
    check('cat.id === "b3"' in app_js,
          "app.js now compares cat.id against the current taxonomy's 'b3' "
          "(Group B: Regulatory & Authority Thresholds, the Governance category)")

    section("2. DOC_KEYS / DOC_TO_CATS: THE PARALLEL-ARRAY INVARIANT")

    nf_js = read("assets/js/neural_flow.js")
    doc_keys_m = re.search(r"var DOC_KEYS = \[([\s\S]*?)\];", nf_js)
    doc_to_cats_m = re.search(r"var DOC_TO_CATS = \[([\s\S]*?)\];", nf_js)
    check(bool(doc_keys_m) and bool(doc_to_cats_m),
          "both DOC_KEYS and DOC_TO_CATS are still findable by this test's own parser")
    doc_keys = re.findall(r"'([a-z_]+)'", doc_keys_m.group(1))
    doc_to_cats_rows = re.findall(r"\[[0-9,\s]*\]", doc_to_cats_m.group(1))

    # Self-test: a synthetic mismatch (one array one entry longer) IS caught by this equality
    # check before trusting it against the real arrays.
    check(len(["a", "b", "c"]) != len(["a", "b"]),
          "self-test: the length-equality check can distinguish unequal lengths")

    check(len(doc_keys) == len(doc_to_cats_rows),
          "DOC_KEYS and DOC_TO_CATS have the same number of entries",
          f"DOC_KEYS={len(doc_keys)} DOC_TO_CATS={len(doc_to_cats_rows)}")
    check(len(doc_keys) == 27, "DOC_KEYS has exactly 27 entries (the current DOC_TYPES count)",
          str(len(doc_keys)))

    section("3. EVERY DIAGRAM/UI DOC KEY IS IN THE SERVER'S CURRENT VOCABULARY")

    # Self-test: an obviously-fake type is NOT in DOC_TYPES, proving membership testing here can
    # fail before it is trusted against the real key lists.
    check("this_type_does_not_exist" not in DOC_TYPES,
          "self-test: a fake type is correctly absent from DOC_TYPES")

    unknown_in_diagram = sorted(set(doc_keys) - set(DOC_TYPES))
    check(not unknown_in_diagram,
          "every neural_flow.js DOC_KEYS entry is a current DOC_TYPES member",
          str(unknown_in_diagram))
    check(set(doc_keys) == set(DOC_TYPES),
          "neural_flow.js DOC_KEYS is exactly the current DOC_TYPES set (no key retired from "
          "the vocabulary still lingers, and nothing current is missing a row)",
          f"diagram-only={sorted(set(doc_keys) - set(DOC_TYPES))} "
          f"vocab-only={sorted(set(DOC_TYPES) - set(doc_keys))}")

    sig_js = read("assets/js/signals.js")
    groups_m = re.search(r"const DOC_TYPE_GROUPS = \[([\s\S]*?)\];\s*\n\s*// flat list", sig_js)
    check(bool(groups_m), "DOC_TYPE_GROUPS is still findable by this test's own parser")
    dropdown_keys = re.findall(r'\[\s*"([a-z_]+)"', groups_m.group(1))
    allowed = set(DOC_TYPES) | set(UI_ONLY_DOC_TYPES)
    unknown_in_dropdown = sorted(set(dropdown_keys) - allowed)
    check(not unknown_in_dropdown,
          "every signals.js upload-dropdown key is DOC_TYPES or UI_ONLY_DOC_TYPES",
          str(unknown_in_dropdown))
    check(set(dropdown_keys) == allowed,
          "the dropdown offers exactly DOC_TYPES + UI_ONLY_DOC_TYPES (no retired 'rfi' / bare "
          "'submittal' entry left offering a type the server will never classify into)",
          f"dropdown-only={sorted(set(dropdown_keys) - allowed)} "
          f"missing-from-dropdown={sorted(allowed - set(dropdown_keys))}")

    section("4. THE RFI ROW: THE LOG, NOT THE RETIRED INDIVIDUAL FORM")

    check("rfi_log" in doc_keys and "rfi" not in doc_keys,
          "the diagram's RFI row is keyed on 'rfi_log', and the retired 'rfi' row is gone "
          "(not repointed onto rfi_log, which already had its own correct row)")

    section("5. THE SUBMITTAL ROW: KEYED ON THE CANONICAL NAME")

    check("submittal_register" in doc_keys and "submittal" not in doc_keys,
          "the diagram's submittal row is keyed on 'submittal_register', the canonical name a "
          "classified/stored docType actually carries")

    section("6. CLASSIFY_HINTS: DESIGN-ENGAGEMENT RFI-LOG WORDING")

    # Self-test against the hints text as it read before this fix (reconstructed), proving the
    # phrase-presence check can fail.
    OLD_HINTS = (
        "Match on content: pay application has contract sum and amount paid; "
        "monthly report has EV/AC/PV; "
        "an RFI log lists requests for information with totals; OAC minutes has meeting "
        "attendees; change order has revised contract sum; "
        "NCR log has non-conformance; cost report has indirect/material cost; "
        "safety report has OSHA incidents."
    )
    check("design query" not in OLD_HINTS.lower(),
          "self-test: the pre-fix hints text does NOT carry the design-query wording")
    check("design query" in CLASSIFY_HINTS.lower(),
          "CLASSIFY_HINTS now names 'design query' titled logs as the same RFI-log type")
    check("owner decision" in CLASSIFY_HINTS.lower(),
          "CLASSIFY_HINTS now names 'owner decision' titled logs as the same RFI-log type")
    check("rfi log" in CLASSIFY_HINTS.lower(),
          "the original RFI-log content hint (totals) survives the rewrite")

    section("7. CLASSIFY_HINTS: SCHEDULE OF VALUES vs PAY APPLICATION")

    check("schedule of values" not in OLD_HINTS.lower(),
          "self-test: the pre-fix hints text had NO schedule_of_values clause at all — this is "
          "the exact gap the audit found")
    check("schedule of values" in CLASSIFY_HINTS.lower(),
          "CLASSIFY_HINTS now has a schedule_of_values clause")
    # The distinguishing structure, not just a description of one document in isolation: SoV
    # named as a line-item breakdown, and explicitly said to carry NEITHER of pay application's
    # two identifying fields.
    check("line item" in CLASSIFY_HINTS.lower(),
          "the schedule_of_values clause names its line-item structure")
    check("no amount paid" in CLASSIFY_HINTS.lower() or "carries no" in CLASSIFY_HINTS.lower(),
          "the schedule_of_values clause states what it does NOT carry, "
          "set against pay_application's own fields")
    check("billing period" in CLASSIFY_HINTS.lower(),
          "pay_application's clause now names a billing period, "
          "the field schedule_of_values lacks")
    check("amount paid" in CLASSIFY_HINTS.lower(),
          "pay_application's clause still names amount paid (the original hint's content "
          "survives, sharpened rather than replaced)")

    section("8. DOC_NOT_APPLICABLE: THE THREE CONFIRMED-ABSENT TYPES, AND ONLY THOSE THREE")

    not_appl_m = re.search(r"var DOC_NOT_APPLICABLE = \{([\s\S]*?)\};", nf_js)
    check(bool(not_appl_m), "DOC_NOT_APPLICABLE is findable by this test's own parser")
    not_appl_keys = set(re.findall(r"'([a-z_]+)':\s*true", not_appl_m.group(1)))
    EXPECTED = {"past_performance_report", "historical_data", "commissioning_report"}
    # Self-test: a wrong set does not equal EXPECTED, proving this equality check can fail.
    check({"past_performance_report"} != EXPECTED,
          "self-test: an incomplete set is correctly distinguished from the expected set")
    check(not_appl_keys == EXPECTED,
          "DOC_NOT_APPLICABLE names exactly the three creator-confirmed-absent types, "
          "no more and no fewer",
          str(sorted(not_appl_keys)))
    check(not_appl_keys.issubset(set(doc_keys)),
          "every DOC_NOT_APPLICABLE key is an actual DOC_KEYS row (nothing orphaned)")
    check(not_appl_keys.issubset(set(DOC_TYPES)),
          "every DOC_NOT_APPLICABLE key is a real, current DOC_TYPES member "
          "(not a typo'd or retired string)")

    section("9. THE NOT-APPLICABLE STATE READS AS THE EXISTING NotRelevant COLOUR, NOT A NEW ONE")

    check("COL.NotRelevant" in nf_js, "COL.NotRelevant (the existing blue not-relevant colour) "
          "is referenced in neural_flow.js")
    check(re.search(r"notApplicable\s*=\s*!uploaded\s*&&\s*!!DOC_NOT_APPLICABLE\[key\]", nf_js)
          is not None,
          "the not-applicable state is gated on !uploaded — a document that WAS uploaded still "
          "lights normally, even if it is one of the three usually-absent types")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — a crash must print a FAILING result line
        import traceback
        traceback.print_exc()
        check(False, f"suite crashed: {type(exc).__name__}: {exc}")
    finish()
