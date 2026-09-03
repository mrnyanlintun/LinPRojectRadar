"""
RUN 126. THE REGISTER STATES ITS OWN ROW COUNT, AND A SHORT REGISTER IS REFUSED.

A CHECK SCRIPT, NOT A PYTEST MODULE -- `server/tools/` holds scripts by convention; under
pytest this file reports "no tests ran". Run it as:

    cd server && python tools/test_run126_register_row_count.py

NO MODEL CALL IS MADE OR SIMULATED. There is no key in this environment and `StubExtractor`
refuses an unrecorded sha256 rather than inventing an extraction. What serves in a model's place
is a CONSTRUCTED REPLY: a dict of exactly the shape `parse_json_response` returns, handed to the
same `validate_register_row_counts` that `extract_many.run` calls, and -- for the two truncation
proofs -- a raw text body handed to `describe_json_truncation` and a payload handed to the
provider clients' own truncation branches. Every count below names the fixture it came from.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import ai_provider
from app.extraction_client import (
    describe_json_truncation, extraction_contract_fingerprint, parse_json_response,
    TruncatedResponseError, extract_many, StubExtractor,
)
from app.extraction_fields import (
    COUNTED_REGISTERS, REGISTER_ROW_COUNT_FIELD, UNCOUNTED_REGISTERS, _EXTRACTION_FIELDS,
    extraction_fields_for,
)
from app.extraction_merge import RegisterRowCountError, validate_register_row_counts

FAILURES: list[str] = []


def check(label: str, cond: bool, detail: str = "") -> None:
    print(("  ok   " if cond else "  FAIL ") + label + (f"  [{detail}]" if detail else ""))
    if not cond:
        FAILURES.append(label)


# ---------------------------------------------------------------------- the fixtures
#
# FIXTURE `QUALITY_26`: an inspection report's `quality_requirements_json` as the document
# prints it -- 26 requirement rows, the register size Run 124 measured the output budget
# against. The reply states 26 and returns 26.
def _rows(n: int, prefix: str = "REQ") -> list[dict]:
    return [{"Item": f"{prefix}-{i:03d}", "Requirement": f"requirement {i}", "Result": "Pass"}
            for i in range(1, n + 1)]


QUALITY_26 = {
    REGISTER_ROW_COUNT_FIELD: {"quality_requirements_json": 26},
    "quality_requirements_json": _rows(26),
    "quality_register_id": "QA-2026-03",
}

# FIXTURE `QUALITY_26_SHORT_BY_ONE`: the SAME reply with the last row removed and the stated
# count untouched. One row, not eight: a check proven only on a large discrepancy is not proven.
QUALITY_26_SHORT_BY_ONE = dict(QUALITY_26, quality_requirements_json=_rows(25))

# FIXTURE `QUALITY_26_LONG_BY_ONE`: the same reply with a 27th row added, count untouched.
QUALITY_26_LONG_BY_ONE = dict(QUALITY_26, quality_requirements_json=_rows(27))

# FIXTURE `QUALITY_26_NO_COUNT`: the array with the count field absent entirely -- the shape an
# ignored instruction takes.
QUALITY_26_NO_COUNT = {"quality_requirements_json": _rows(26)}

# FIXTURE `SUBMITTAL_46`: the 46-row submittal register Run 124 measured at ~4004 tokens, with
# its FIVE sibling `*_json` fields present in the three shapes that matter -- a counted register
# returned whole, the legend as an OBJECT, and two override tables, one absent and one `[]`.
SUBMITTAL_46 = {
    REGISTER_ROW_COUNT_FIELD: {"submittal_decisions_json": 46, "trade_attribution_json": 0},
    "submittal_decisions_json": _rows(46, "SUB"),
    "submittal_disposition_legend_json": {"A": "Approved", "R": "Revise and resubmit"},
    "rejected_blocking_past_deadline_json": [],
    "trade_attribution_json": [],
    "submittal_reporting_period": "March 2026",
}


def main() -> int:
    print(__doc__.strip().splitlines()[0])

    # =================================================================== 0. the lists
    print("\n0. WHICH REGISTERS ARE COUNTED, AND WHICH ARE NOT")
    all_json = {f for fs in _EXTRACTION_FIELDS.values() for f in fs if f.endswith("_json")}
    check("every *_json field any type asks for is ruled on",
          not (all_json - COUNTED_REGISTERS - UNCOUNTED_REGISTERS),
          f"{len(all_json)} fields, {len(COUNTED_REGISTERS)} counted, "
          f"{len(UNCOUNTED_REGISTERS)} excluded")
    check("the two lists do not overlap", not (COUNTED_REGISTERS & UNCOUNTED_REGISTERS))
    for override in ("open_critical_ncr_json", "hold_point_or_turnover_blocking_ncr_json",
                     "ncr_open_past_contractual_closure_json",
                     "rejected_critical_or_long_lead_late_json",
                     "rejected_blocking_past_deadline_json",
                     "critical_quality_failures_json"):
        check(f"absent-vs-empty override table excluded: {override}",
              override in UNCOUNTED_REGISTERS)
    check("the legend (a mapping) is excluded",
          "submittal_disposition_legend_json" in UNCOUNTED_REGISTERS)
    check("the calendar NAME list is excluded",
          "schedule_calendars_json" in UNCOUNTED_REGISTERS)
    check("the calendar DEFINITIONS are counted",
          "schedule_calendar_json" in COUNTED_REGISTERS)
    carriers = [t for t, f in _EXTRACTION_FIELDS.items() if REGISTER_ROW_COUNT_FIELD in f]
    check("the count field is asked of every type carrying a counted register",
          sorted(carriers) == sorted(t for t, f in _EXTRACTION_FIELDS.items()
                                     if any(x in COUNTED_REGISTERS for x in f)),
          f"{len(carriers)} document types")
    check("it is the FIRST field asked for, so the prompt names it before any register",
          all(extraction_fields_for(t)[0] == REGISTER_ROW_COUNT_FIELD for t in carriers))
    check("a type with no counted register is not asked for it",
          REGISTER_ROW_COUNT_FIELD not in extraction_fields_for("risk_register"))

    # =============================================== 1. the check passes a correct register
    print("\n1. A CORRECT REGISTER PASSES (fixture QUALITY_26: 26 stated, 26 returned)")
    try:
        validate_register_row_counts(QUALITY_26, filename="inspection-march.pdf")
        check("26 stated, 26 returned: accepted", True)
    except RegisterRowCountError as exc:
        check("26 stated, 26 returned: accepted", False, str(exc))
    try:
        validate_register_row_counts(SUBMITTAL_46, filename="submittal-register.pdf")
        check("fixture SUBMITTAL_46: 46 stated / 46 returned, legend object, override [] and "
              "override absent, all accepted", True)
    except RegisterRowCountError as exc:
        check("fixture SUBMITTAL_46 accepted", False, str(exc))
    # THE EXCLUSIONS ARE NOT MERELY UNCHECKED -- they are proven inert. A reply whose override
    # table is [] with no count stated must pass, or the tested/not-tested distinction dies.
    try:
        validate_register_row_counts({"open_critical_ncr_json": [],
                                      "critical_quality_failures_json": _rows(3)})
        check("an excluded register with no count stated passes untouched", True)
    except RegisterRowCountError as exc:
        check("an excluded register with no count stated passes untouched", False, str(exc))
    try:
        validate_register_row_counts({"quality_requirements_json": None,
                                      REGISTER_ROW_COUNT_FIELD: {}})
        check("a register returned as null (no such table) needs no count", True)
    except RegisterRowCountError as exc:
        check("a register returned as null needs no count", False, str(exc))

    # ================================================ 2. short by ONE row is refused
    print("\n2. THE FAULT, INTRODUCED: A REGISTER SHORT BY ONE ROW "
          "(fixture QUALITY_26_SHORT_BY_ONE: 26 stated, 25 returned)")
    try:
        validate_register_row_counts(QUALITY_26_SHORT_BY_ONE, filename="inspection-march.pdf")
        check("short by one is refused", False, "IT WAS ACCEPTED")
    except RegisterRowCountError as exc:
        msg = str(exc)
        check("short by one is refused", True)
        check("the refusal names the document", "inspection-march.pdf" in msg)
        check("the refusal names the register", "quality_requirements_json" in msg)
        check("the refusal names the count STATED", "26 rows" in msg)
        check("the refusal names the count RETURNED", "returned 25" in msg)
        check("the refusal says nothing was stored", "Nothing was stored" in msg)
        print("       " + msg)
    # THE FAULT REMOVED: the same reply with the row restored passes again.
    try:
        validate_register_row_counts(QUALITY_26, filename="inspection-march.pdf")
        check("fault removed (row restored): accepted again", True)
    except RegisterRowCountError as exc:
        check("fault removed: accepted again", False, str(exc))

    print("\n2b. THE SAME FAULT AT THE REAL BOUNDARY, through extract_many.run")
    import hashlib
    raw = b"an inspection report whose register the model under-read"
    sha = hashlib.sha256(raw).hexdigest()
    stub = StubExtractor({sha: ("inspection_report", QUALITY_26_SHORT_BY_ONE)})
    res = extract_many(stub, [{"sha256": sha, "content": raw, "mime_type": "application/pdf",
                               "filename": "inspection-march.pdf", "doc_type": None}])[0]
    check("the per-file result is ok=False", res["ok"] is False)
    check("nothing is carried forward as an extraction", res["extraction"] is None)
    check("the PM-visible error is the row-count refusal",
          "quality_requirements_json" in (res["error"] or "")
          and "returned 25" in (res["error"] or ""))
    stub_ok = StubExtractor({sha: ("inspection_report", QUALITY_26)})
    res_ok = extract_many(stub_ok, [{"sha256": sha, "content": raw,
                                     "mime_type": "application/pdf",
                                     "filename": "inspection-march.pdf", "doc_type": None}])[0]
    check("fault removed at the boundary: ok=True", res_ok["ok"] is True, str(res_ok["error"]))

    # ================================================ 3. longer than stated is refused
    print("\n3. LONGER THAN STATED IS ALSO REFUSED "
          "(fixture QUALITY_26_LONG_BY_ONE: 26 stated, 27 returned)")
    try:
        validate_register_row_counts(QUALITY_26_LONG_BY_ONE, filename="inspection-march.pdf")
        check("long by one is refused", False, "IT WAS ACCEPTED")
    except RegisterRowCountError as exc:
        check("long by one is refused", True)
        check("the refusal says it went beyond", "went beyond" in str(exc))
        print("       " + str(exc))

    print("\n3b. THE OTHER TWO SHAPES OF THE SAME CONTRADICTION")
    try:
        validate_register_row_counts(QUALITY_26_NO_COUNT, filename="inspection-march.pdf")
        check("an array with NO count stated is refused", False, "IT WAS ACCEPTED")
    except RegisterRowCountError as exc:
        check("an array with NO count stated is refused", True)
        print("       " + str(exc))
    try:
        validate_register_row_counts(
            {REGISTER_ROW_COUNT_FIELD: {"quality_requirements_json": 26}},
            filename="inspection-march.pdf")
        check("a count stated with NO array returned is refused", False, "IT WAS ACCEPTED")
    except RegisterRowCountError as exc:
        check("a count stated with NO array returned is refused", True)
        print("       " + str(exc))
    try:
        validate_register_row_counts({REGISTER_ROW_COUNT_FIELD:
                                      {"quality_requirements_json": True},
                                      "quality_requirements_json": _rows(1)})
        check("a boolean is not read as a count of one", False, "IT WAS ACCEPTED")
    except RegisterRowCountError as exc:
        check("a boolean is not read as a count of one", True)

    # ================================ 4. both truncation defences still fire, unchanged
    print("\n4. THE TWO EXISTING TRUNCATION DEFENCES, RE-ESTABLISHED (not assumed)")

    class _Payload:
        def __init__(self, payload):
            self.payload = payload

    anth = ai_provider.AnthropicClient.__new__(ai_provider.AnthropicClient)
    anth.cfg = ai_provider.ProviderConfig(
        role="extraction", provider="anthropic", wire="anthropic", model="m", url="u",
        key_env="ANTHROPIC_API_KEY")
    anth._key = ""
    anth._request = lambda body, headers: {"stop_reason": "max_tokens", "content": []}
    try:
        anth.complete([{"type": "text", "text": "p"}], 8192)
        check("ai_provider AnthropicClient raises on stop_reason=max_tokens", False)
    except ai_provider.ProviderTruncated as exc:
        check("ai_provider AnthropicClient raises on stop_reason=max_tokens", True, str(exc))

    oai = ai_provider.OpenAICompatClient.__new__(ai_provider.OpenAICompatClient)
    oai.cfg = ai_provider.ProviderConfig(
        role="extraction", provider="openai", wire="openai", model="m", url="u",
        key_env="OPENAI_API_KEY")
    oai._key = ""
    oai._request = lambda body, headers: {"choices": [{"finish_reason": "length",
                                                       "message": {"content": ""}}]}
    try:
        oai.complete([{"type": "text", "text": "p"}], 8192)
        check("ai_provider OpenAICompatClient raises on finish_reason=length", False)
    except ai_provider.ProviderTruncated as exc:
        check("ai_provider OpenAICompatClient raises on finish_reason=length", True, str(exc))

    # A MID-ARRAY CUT. The 26-row register cut off inside its ninth row: the shape that must
    # still reach TruncatedResponseError and NOT the row-count check, because it never parses.
    whole = json.dumps({REGISTER_ROW_COUNT_FIELD: {"quality_requirements_json": 26},
                        "quality_requirements_json": _rows(26)})
    cut = whole[:whole.index('"Item": "REQ-009"') + 12]
    check("describe_json_truncation names where the mid-array cut stopped",
          describe_json_truncation(cut) is not None, describe_json_truncation(cut) or "")
    try:
        parse_json_response(cut)
        check("a mid-array cut still raises TruncatedResponseError", False)
    except TruncatedResponseError as exc:
        check("a mid-array cut still raises TruncatedResponseError", True)
        print("       " + str(exc)[:150])
    check("a COMPLETE reply is still not called truncated",
          describe_json_truncation(whole) is None)

    # ===================================================== 5. the fingerprint moves, once
    print("\n5. THE EXTRACTION CONTRACT FINGERPRINT MOVES FOR REGISTER-BEARING TYPES")
    # The BEFORE values are the sha256 of the prompt as `e4a263e` issued it, recorded here.
    before = {
        "inspection_report":
            "c3a32e0ab1fb20533ed4252a5cd73a9c73630fb672c598b76bf6c648a4491684",
        "submittal_register":
            "a1a72d970b66a91e5fd13c8d6fd3998387219068f51a4e803633860974ef152e",
        "schedule_update":
            "d37a71d9316d882b06e045c7761014c7c7b85b67ffdbf147a93d579b04b6d387",
        "ncr_log":
            "e6d629e8a5960ebb9f6d1cf7a09eb3f952f16a2b9355839d1bd1684f88d42f3c",
        # A TYPE WITH NO COUNTED REGISTER IS NOT RESTALED, and that is the point of the row.
        "risk_register":
            "d195c7cb63b5a52979f827a5d1b01c5de53ae118aeeac9dc208b3ab186c17ec9",
    }
    for dtype, old in before.items():
        now = extraction_contract_fingerprint(dtype)
        moved = now != old
        should = REGISTER_ROW_COUNT_FIELD in extraction_fields_for(dtype)
        check(f"{dtype}: fingerprint {'moved' if should else 'unchanged'}", moved == should,
              f"{old[:12]} -> {now[:12]}")

    print()
    if FAILURES:
        print(f"FAILED: {len(FAILURES)}")
        for f in FAILURES:
            print("  - " + f)
        return 1
    print("run126 register row count: all checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
