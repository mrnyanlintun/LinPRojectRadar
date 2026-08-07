#!/usr/bin/env python3
"""
The activity table read by the reader, at any size; truncation reported as truncation; the
upload record that survives its dialog; and signals generated for every period in order.

WHAT THIS SUITE PROTECTS, in the order the defects were found.

1. THE ROW COUNT IS UNBOUNDED, AND THE COST DOES NOT DEPEND ON IT. A real schedule document
   carrying twenty-nine activities in an eleven-column table failed extraction three times with
   `model response was not JSON` on a response that was valid JSON cut off mid-key. The model had
   been asked to serialise the whole table into one field and ran out of output tokens at the
   seventh scalar key, before reaching it. Twenty-nine is small; a real construction schedule
   carries hundreds or thousands, so no output cap is large enough. The checks below measure the
   model call for a 29-row table and for a 500-row table and assert both the CALL COUNT and the
   PROMPT SIZE are the same, because "the number does not matter" has to be demonstrated.

2. A TRUNCATED RESPONSE SAYS SO, AND NAMES WHERE IT STOPPED. "Not JSON" describes a model that
   answered with prose. It cost three retries at a failure that reproduces identically every
   time. The exact prefix the real failure produced is asserted here verbatim.

3. WHAT FAILED IS READABLE AFTER THE DIALOG IS GONE, AND RETRIES PER DOCUMENT. Extraction
   refuses a whole document rather than storing part of it, so a failure leaves NO row and the
   document is simply absent. The attempt is therefore recorded when it is made.

4. EVERY PERIOD COMPUTES, IN ORDER, AND AN EARLIER PERIOD STAYS BYTE-IDENTICAL. Same comparison
   `test_schedule_milestones.py` and `test_period_series.py` state: the stored row's analytical
   content serialised with `json.dumps(sort_keys=True)` and compared as bytes, with `result_id`
   and `computed_at` excluded BY NAME because a recompute is a new append-only row and is
   required to have a new id.

5. A RESEARCH ACCOUNT IS REFUSED THE ALL-PERIODS CONTROL SERVER-SIDE. Called directly, not by
   checking that a button is hidden.

REAL DOCUMENT VERSUS CONSTRUCTED. The real document this work was driven by is owner-supplied
and is NOT in this repository, so this suite cannot carry it. What it carries is a document of
the SAME SHAPE: the real extract's eleven column headings verbatim (`Activity ID`,
`Activity name`, `BL start`, `BL finish`, `Actual start`, `Actual finish`, `Forecast start`,
`Forecast finish`, `% complete`, `Rem. workdays`, `TF workdays`), the same two-finish-column
layout where exactly one of Actual finish and Forecast finish is filled per row and the other
holds an em-dash placeholder, and the same twenty-nine data rows' worth of structure. The
activity identifiers and names are constructed. Set REAL_SCHEDULE_DOCX to a real file's path and
the suite additionally runs every reader check against it; the report states which results came
from which.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_unbounded_schedule.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import sys
import zipfile
from io import BytesIO
from xml.sax.saxutils import escape

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.docx_text import docx_tables, docx_to_text  # noqa: E402
from app.extraction_client import (  # noqa: E402
    AnthropicExtractor, ExtractionError, StubExtractor, TruncatedResponseError,
    describe_json_truncation, parse_json_response,
)
from app.features import RESEARCH_FORBIDDEN_ACTIONS  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import (  # noqa: E402
    ComputedResult, Participant, ScheduleActivity, UploadAttempt,
)
from app.schedule_activities import (  # noqa: E402
    DISPLAY_RULE, MAX_DRAWN, map_headings, select_for_display,
)
from app.schedule_dates import ACTUAL, FORECAST  # noqa: E402
from app.schedule_table import (  # noqa: E402
    activity_rows_from_document, activity_table_from_document, find_activity_table,
)

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
PASSED = 0
FAILED = 0


def check(ok: bool, label: str, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"  PASS  {label}")
    else:
        FAILED += 1
        print(f"  ****  {label}" + (f"  [{detail}]" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


# --------------------------------------------------------------------------- docx fixtures

_NS = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
_CT = ('<?xml version="1.0" encoding="UTF-8"?><Types '
       'xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
       '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.'
       'relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
       '<Override PartName="/word/document.xml" ContentType="application/vnd.'
       'openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>')
_RELS = ('<?xml version="1.0" encoding="UTF-8"?><Relationships '
         'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
         '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
         'relationships/officeDocument" Target="word/document.xml"/></Relationships>')


def _p(text: str) -> str:
    return f'<w:p><w:r><w:t xml:space="preserve">{escape(str(text))}</w:t></w:r></w:p>'


def _tbl(rows) -> str:
    out = []
    for row in rows:
        cells = "".join(f"<w:tc>{_p(c)}</w:tc>" for c in row)
        out.append("<w:tr>" + cells + "</w:tr>")
    return "<w:tbl>" + "".join(out) + "</w:tbl>"


def _docx(blocks) -> bytes:
    doc = (f'<?xml version="1.0" encoding="UTF-8"?><w:document {_NS}><w:body>'
           + "".join(blocks) + "</w:body></w:document>")
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CT)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/document.xml", doc)
    return buf.getvalue()


# The real extract's eleven column headings, verbatim. The headings are the export format, not
# the project's data, and the mapping has to be tested against the strings a real scheduling
# tool actually writes.
HEADINGS = ["Activity ID", "Activity name", "BL start", "BL finish", "Actual start",
            "Actual finish", "Forecast start", "Forecast finish", "% complete",
            "Rem. workdays", "TF workdays"]

# The header block a schedule status document carries above the activity table. Present so the
# recogniser has to pass over a table that is NOT the activity table, which is what it does on
# the real document.
HEADER_BLOCK = _tbl([
    ["Project", "North Concourse Rehabilitation", "", ""],
    ["Contract", "PRJ-002", "Document", "SCH-U01-ACT"],
    ["Period", "12 January 2026 through 28 February 2026", "Issue date", "3 March 2026"],
    ["Contractor", "A Contractor, LLC", "Data date", "28 February 2026"],
])


def activity_row(n: int, *, finished: bool, forecast_finish: str,
                 baseline_finish: str) -> list:
    """
    One data row in the real layout: exactly one of Actual finish / Forecast finish is filled
    and the other holds the em-dash placeholder the source prints.
    """
    key = f"ACT-{n:04d}"
    if finished:
        return [key, f"Activity {n}", "12-Jan-26", baseline_finish, "12-Jan-26",
                forecast_finish, "--", "--", "100.0%", "0", "0"]
    return [key, f"Activity {n}", "12-Jan-26", baseline_finish, "12-Jan-26", "--", "--",
            forecast_finish, "40.0%", "12", "5"]


def schedule_docx(rows: list) -> bytes:
    return _docx([
        _p("SCHEDULE ACTIVITY STATUS"),
        _p("Update U01 - Selected Level 3 activities"),
        HEADER_BLOCK,
        _tbl([HEADINGS] + rows),
        _p("Selected Level 3 extract. TF = total float in workdays."),
    ])


def table_of(n: int, *, shift_days: int = 0) -> list:
    """`n` activity rows. Every fourth is finished; the rest carry a forecast finish."""
    rows = []
    for i in range(1, n + 1):
        day = (i % 27) + 1
        month = ((i // 27) % 9) + 3
        finish = f"{day:02d}-{['Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov'][month - 3]}-26"
        moved = f"{min(28, day + shift_days):02d}-" \
                f"{['Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov'][month - 3]}-26"
        rows.append(activity_row(i, finished=(i % 4 == 0), forecast_finish=moved,
                                 baseline_finish=finish))
    return rows


DOC_29 = schedule_docx(table_of(29))
DOC_500 = schedule_docx(table_of(500))

try:
    print("=" * 78)
    print("1. THE ROW COUNT IS UNBOUNDED: 29 rows and 500 rows, read the same way")
    print("=" * 78)

    tables_29 = docx_tables(DOC_29)
    check(len(tables_29) == 2,
          "the reader returns every table as a grid: the header block and the activity table",
          str(len(tables_29)))

    t29 = activity_table_from_document(DOC_29, "", "schedule.docx")
    check(t29 is not None and t29.row_count == 29,
          "the 29-row activity table is recognised, with 29 data rows and not 30",
          str(t29.row_count if t29 else None))
    check(t29 is not None and t29.headings == HEADINGS,
          "and its eleven column headings are the document's own, in order",
          str(t29.headings if t29 else None))
    check(t29 is not None and t29.index == 1,
          "the header block above it is NOT mistaken for the activity table: it resolves no "
          "identity column and no finish column, so the recogniser passes over it",
          str(t29.index if t29 else None))

    cmap = t29.column_map
    check(cmap.get("activity_key") == "Activity ID"
          and cmap.get("description") == "Activity name"
          and cmap.get("baseline_start") == "BL start"
          and cmap.get("baseline_finish") == "BL finish"
          and cmap.get("percent_complete") == "% complete",
          "the column mapping is resolved ONCE per table, from the headings, in code",
          str(cmap))
    check(cmap.get("current_finish") == "Actual finish",
          "and the current finish prefers the ACTUAL column over the forecast one, because "
          "where both are printed the actual is the fact",
          str(cmap))

    rows29 = activity_rows_from_document(DOC_29, "", "schedule.docx")
    check(len(rows29) == 29, "all 29 rows parse; none is dropped", str(len(rows29)))
    check(all(r["usable_for_trend"] for r in rows29),
          "and every one carries a readable finish date despite the em-dash placeholder in the "
          "column it did not use",
          str([r["activity_key"] for r in rows29 if not r["usable_for_trend"]]))
    finished = [r for r in rows29 if r["current_finish_kind"] == ACTUAL]
    check(len(finished) == 7 and all(r["percent_complete"] == 100.0 for r in finished),
          "the rows finished under the 'Actual finish' heading are marked ACTUAL, not forecast: "
          "the column states the kind exactly as a trailing marker would",
          str(len(finished)))
    check(sum(1 for r in rows29 if r["current_finish_kind"] == FORECAST) == 22,
          "and the rest stay forecasts, which are the only dates that can slip")

    rows500 = activity_rows_from_document(DOC_500, "", "schedule.docx")
    check(len(rows500) == 500,
          "a 500-row table reads all 500 rows through exactly the same path",
          str(len(rows500)))
    check(all(r["current_finish"] for r in rows500),
          "with every row carrying a finish date")

    print()
    print("-" * 78)
    print("1b. AND IT COSTS THE SAME. Measured, not claimed.")
    print("-" * 78)

    class Recorder:
        """A stand-in for the HTTPS POST, counting calls and measuring what was sent."""

        def __init__(self) -> None:
            self.calls: list[dict] = []

        def __call__(self, prompt: str, content_block: dict, max_tokens: int) -> str:
            self.calls.append({"prompt": prompt,
                               "text": content_block.get("text", ""),
                               "max_tokens": max_tokens})
            return json.dumps({"planned_percent_complete": 40.0, "data_date": "2026-02-28",
                               "activities_planned": 29})

    def measure(raw: bytes) -> dict:
        rec = Recorder()
        ex = AnthropicExtractor("key-not-used")
        ex._post = rec  # noqa: SLF001 — the network boundary is the thing being stubbed
        doc_type, fields, _c = ex.extract_with_confidence(raw, "", "schedule.docx",
                                                          "schedule_update")
        return {"calls": len(rec.calls), "prompt": rec.calls[-1]["prompt"],
                "text": rec.calls[-1]["text"], "fields": fields}

    m29, m500 = measure(DOC_29), measure(DOC_500)

    check(m29["calls"] == 1 and m500["calls"] == 1,
          "ONE model call for the 29-row document and ONE for the 500-row document",
          f"{m29['calls']} vs {m500['calls']}")
    delta = abs(len(m29["text"]) - len(m500["text"]))
    check(delta <= 8,
          f"and the text sent to the model is the same size either way: "
          f"{len(m29['text'])} characters for 29 rows, {len(m500['text'])} for 500, a "
          f"difference of {delta} (the digits of the row count in the elision note)",
          str(delta))
    check(m29["prompt"] == m500["prompt"],
          "the prompt is byte-identical between the two, because the field list no longer "
          "depends on the document's size")
    check("milestones_json" not in m29["prompt"],
          "milestones_json is NOT asked for when the reader has the table: the scalar fields "
          "get the whole output budget, which is the response that ran out")
    check("ACT-0007" not in m29["text"] and "ACT-0400" not in m500["text"],
          "and no activity row is sent to the model at all")
    check("ACTIVITY TABLE: 29 data row(s)" in m29["text"]
          and "ACTIVITY TABLE: 500 data row(s)" in m500["text"],
          "what stands in their place SAYS SO, with the count and the headings, so a short "
          "answer can never be traced to a table the model silently never saw",
          m29["text"][-200:])
    check("Activity ID" in m29["text"] and "TF workdays" in m29["text"],
          "the header row survives the elision, so the model can still see the document has a "
          "schedule")

    print()
    print("-" * 78)
    print("1c. Which rows are DRAWN: the rule, stated and bounded")
    print("-" * 78)

    later = activity_rows_from_document(schedule_docx(table_of(500, shift_days=3)), "",
                                        "schedule.docx")
    display = select_for_display(later, rows500)
    check(display["total"] == 500, "the display is computed over all 500 stored rows",
          str(display["total"]))
    check(len(display["shown"]) <= MAX_DRAWN,
          f"but never draws more than {MAX_DRAWN} of them",
          str(len(display["shown"])))
    check(display["not_shown"] == 500 - len(display["shown"]) and display["not_shown"] > 400,
          "and it says how many are stored and not drawn rather than implying the schedule is "
          "short", str(display["not_shown"]))
    check(display["rule"] == DISPLAY_RULE and "moved later" in display["rule"],
          "the rule that decided is returned beside the selection, not left to be inferred")
    check(all(a["slip_days"] and a["slip_days"] > 0 for a in display["shown"][:5]),
          "the rows that MOVED come first, ordered by how far",
          str([a["slip_days"] for a in display["shown"][:5]]))

    unmoved = select_for_display(rows500, rows500)
    check(all(a["slip_days"] is None for a in unmoved["shown"]),
          "a schedule compared with itself claims no movement at all")
    arrived = select_for_display(rows29, [])
    check(all(a["slip_days"] is None for a in arrived["shown"]),
          "and an activity with no previous period has ARRIVED, not moved: absence is never "
          "read as movement")
    check(select_for_display([], [])["shown"] == [],
          "an empty schedule draws nothing and claims nothing")

    print()
    print("=" * 78)
    print("2. A TRUNCATED RESPONSE IS REPORTED AS TRUNCATION, naming where it stopped")
    print("=" * 78)

    # The real failure's response prefix, as it was recorded. Valid JSON, cut off mid-key.
    REAL_TRUNCATION = ('{\n "planned_percent_complete": null,\n "actual_percent_complete": 41.2,'
                       '\n "data_date": "2026-02-28",\n "total_float_days": 0,\n '
                       '"critical_path_length": 118,\n "activities_planned": 29,\n '
                       '"activities_constrain')

    try:
        parse_json_response(REAL_TRUNCATION)
        check(False, "the real truncated response raises")
    except TruncatedResponseError as exc:
        msg = str(exc)
        check(True, "the real truncated response raises TruncatedResponseError, not a "
                    "generic extraction error")
        check("cut off" in msg and "ran out of output space" in msg,
              "and the message says the answer was CUT OFF, not that it was not JSON", msg)
        check("activities_constrain" in msg,
              "naming WHAT WAS BEING READ when it stopped: the partial field name itself", msg)
        check("activities_planned" in msg,
              "and the last field it completed, so a reader can see how far it got", msg)
        check("Retrying will stop in the same place" in msg,
              "and it says retrying will not help, which is the fact three retries established",
              msg)
    except ExtractionError as exc:
        check(False, "the real truncated response raises TruncatedResponseError", str(exc))

    check(isinstance(TruncatedResponseError("x"), ExtractionError),
          "TruncatedResponseError is an ExtractionError, so every existing caller that handles "
          "one still handles this without a new branch")

    cases = [
        ('{"a": 1, "b": "half a val', "b", "cut off inside a string VALUE names its field"),
        ('{"a": 1, "b', "a", "cut off inside a field NAME names the last completed field"),
        ('{"a": 1, "b": [1, 2', "b", "cut off inside a nested array"),
        ('{"a": {"b": 2', "b", "cut off inside a nested object"),
    ]
    for text, expect, why in cases:
        got = describe_json_truncation(text)
        check(got is not None and expect in got, f"{why}: {text!r}", str(got))

    complete = ['{"a": 1}', '{"a": [1, 2], "b": {"c": null}}', "[]", "{}", '"a string"', "null"]
    for text in complete:
        check(describe_json_truncation(text) is None,
              f"a COMPLETE value is not called truncated: {text!r}",
              str(describe_json_truncation(text)))
    check(describe_json_truncation('{"a": "}"}') is None,
          "a brace inside a quoted string does not fool the scanner")
    check(describe_json_truncation('{"a": "\\""}') is None,
          "and neither does an escaped quote")

    # The failure that IS "not JSON" must keep saying so. Making everything read as truncation
    # would be the same defect with the words swapped.
    try:
        parse_json_response("I am sorry, I cannot read this document.")
        check(False, "prose still raises")
    except TruncatedResponseError:
        check(False, "prose must NOT be reported as truncation")
    except ExtractionError as exc:
        check("was not JSON" in str(exc),
              "a model that answered with PROSE is still reported as not JSON: the two failures "
              "stay distinguishable", str(exc))

    print()
    print("=" * 78)
    print("3. THE REAL PIPELINE: the schedule stored per activity, per period")
    print("=" * 78)

    ADMIN = "unbounded-admin-token"
    PRJ = "PRJ-UNBOUND"

    SCALARS = {"planned_percent_complete": 40.0, "data_date": "2026-02-28",
               "activities_planned": 29}
    P2_DOC = schedule_docx(table_of(29, shift_days=3))
    RECORDED = {
        hashlib.sha256(DOC_29).hexdigest(): ("schedule_update", dict(SCALARS)),
        hashlib.sha256(P2_DOC).hexdigest(): (
            "schedule_update", {**SCALARS, "data_date": "2026-03-31"}),
        hashlib.sha256(DOC_500).hexdigest(): ("schedule_update", dict(SCALARS)),
    }

    class FailingStub(StubExtractor):
        """The recorded stub, plus a set of hashes it refuses with a stated reason."""

        def __init__(self, recorded, failures) -> None:
            super().__init__(recorded)
            self._failures = dict(failures)

        def extract_with_confidence(self, raw, mime_type, filename, doc_type=None):
            sha = hashlib.sha256(raw).hexdigest()
            if sha in self._failures:
                raise ExtractionError(self._failures[sha])
            return super().extract_with_confidence(raw, mime_type, filename, doc_type)

    BROKEN = b"%PDF-1.4 this document cannot be read\n"
    BROKEN_SHA = hashlib.sha256(BROKEN).hexdigest()
    TRUNCATION_REASON = ("the model ran out of output space before it finished answering: the "
                         "model's answer was cut off while writing a field name, after "
                         "'activities_planned'; the name it had reached was "
                         "'activities_constrain'. Retrying will stop in the same place; the "
                         "answer has to be made smaller.")
    set_extractor_override(FailingStub(RECORDED, {BROKEN_SHA: TRUNCATION_REASON}))

    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="UNB-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == PRJ)) is None:
            s.add(Project(legacy_id=PRJ, doc={"id": PRJ, "name": "Unbounded One",
                                              "signals": {}, "events": []}))
        s.commit()

    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": "UNB-PM", "role": "Participant",
                    "account_type": "operational"})
    pm_id = created["participant_id"]
    pm = post({"action": "researchlogin",
               "access_token": created["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": admin, "id": PRJ,
          "participant_id": pm_id, "project_role": "PM"})

    def upload(period: int, name: str, raw: bytes) -> dict:
        return post({"action": "projectupload", "session_token": pm, "id": PRJ,
                     "period": period,
                     "documents": [{"filename": name, "mimeType":
                                    "application/vnd.openxmlformats-officedocument."
                                    "wordprocessingml.document",
                                    "dataBase64": b64(raw)}]})

    up1 = upload(1, "schedule-u01.docx", DOC_29)
    check(up1.get("ok") is True, "the 29-activity document uploads and extracts", str(up1)[:200])
    # PERIOD 1 IS COMPUTED NOW, WHILE IT IS THE ONLY PERIOD THAT EXISTS. That is what makes the
    # byte comparison in part 5 a real constraint: the row it is compared against was produced
    # before any later period had been uploaded, so a later period leaking into period 1's
    # inputs changes the recomputed row and the comparison fails.
    check(post({"action": "projectcompute", "session_token": pm, "id": PRJ,
                "period": 1}).get("ok") is True,
          "and period 1 is computed while it is the only period the project has")
    check(up1["files"][0]["status"] == "extracted",
          "reported as extracted, with no truncation anywhere on the path",
          str(up1["files"][0]))

    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PRJ))
        acts = s.scalars(select(ScheduleActivity).where(
            ScheduleActivity.project_id == proj.id, ScheduleActivity.period == 1)).all()
    check(len(acts) == 29,
          "and TWENTY-NINE rows reach the per-activity store: one row per activity per period, "
          "never a blob in a field", str(len(acts)))
    check(sum(1 for a in acts if a.current_finish_kind == ACTUAL) == 7,
          "with the actual/forecast distinction intact in storage",
          str(sum(1 for a in acts if a.current_finish_kind == ACTUAL)))

    up500 = upload(3, "schedule-big.docx", DOC_500)
    check(up500.get("ok") is True, "the 500-activity document uploads too", str(up500)[:200])
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PRJ))
        big = s.scalars(select(ScheduleActivity).where(
            ScheduleActivity.project_id == proj.id, ScheduleActivity.period == 3)).all()
    check(len(big) == 500,
          "and FIVE HUNDRED rows reach the store, through the identical path",
          str(len(big)))

    status1 = post({"action": "projectuploadstatus", "session_token": pm, "id": PRJ,
                    "period": 3})
    sched = status1.get("schedule") or {}
    check(sched.get("total") == 500 and len(sched.get("shown") or []) <= MAX_DRAWN,
          "the surface that reads it draws at most a bounded selection of the 500",
          str(sched.get("total")) + "/" + str(len(sched.get("shown") or [])))
    check(sched.get("rule") == DISPLAY_RULE,
          "and states the rule it used, on the response, in words")

    print()
    print("=" * 78)
    print("4. WHAT FAILED IS READABLE AFTER THE DIALOG IS GONE, and retries per document")
    print("=" * 78)

    batch = post({"action": "projectupload", "session_token": pm, "id": PRJ, "period": 2,
                  "documents": [
                      {"filename": "schedule-u02.docx", "mimeType": "application/vnd."
                       "openxmlformats-officedocument.wordprocessingml.document",
                       "dataBase64": b64(P2_DOC)},
                      {"filename": "broken.pdf", "mimeType": "application/pdf",
                       "dataBase64": b64(BROKEN)},
                  ]})
    check(batch.get("ok") is True and batch["summary"]["failed"] == 1,
          "a batch of two where one document fails still stores the other",
          str(batch.get("summary")))

    # The dialog is now gone. Everything below is a FRESH read, of the kind a different person
    # on a different day would make.
    status = post({"action": "projectuploadstatus", "session_token": pm, "id": PRJ, "period": 2})
    failed = status.get("failed") or []
    check(len(failed) == 1 and failed[0]["filename"] == "broken.pdf",
          "the failure is readable afterwards, by filename, from a plain status read",
          str(failed))
    first_error = (failed[0].get("error") or "") if failed else ""
    check(first_error == TRUNCATION_REASON,
          "IN THE WORDS OF THE ACTUAL FAILURE, verbatim, not a category and not "
          "'extraction failed'", first_error[:160])
    check("activities_constrain" in first_error,
          "so the field the response stopped at survives all the way to the reader")

    stored_names = {d["filename"] for d in status["documents"]}
    check("broken.pdf" not in stored_names,
          "and it is NOT derivable from what is stored: the failed document has no row at all, "
          "which is exactly why the attempt had to be recorded when it was made",
          str(sorted(stored_names)))
    check(len(status.get("attempts") or []) == 2,
          "both files in the batch are in the attempt record, the one that worked included",
          str(len(status.get("attempts") or [])))
    check(len({a["batch_id"] for a in status["attempts"]}) == 1,
          "sharing one batch id, so a reader can say which upload they arrived in")

    # RETRY PER DOCUMENT: one file, on its own, not the batch.
    set_extractor_override(FailingStub({**RECORDED,
                                        BROKEN_SHA: ("schedule_update", dict(SCALARS))}, {}))
    retry = post({"action": "projectupload", "session_token": pm, "id": PRJ, "period": 2,
                  "documents": [{"filename": "broken.pdf", "mimeType": "application/pdf",
                                 "dataBase64": b64(BROKEN)}]})
    check(retry.get("ok") is True and retry["summary"]["total"] == 1
          and retry["summary"]["failed"] == 0,
          "the failed document is retried ON ITS OWN, one document in the request, not the "
          "batch of two", str(retry.get("summary")))

    after = post({"action": "projectuploadstatus", "session_token": pm, "id": PRJ, "period": 2})
    check((after.get("failed") or []) == [],
          "and it is no longer outstanding, because its LATEST attempt succeeded")
    check(len(after["attempts"]) == 3,
          "while the failed attempt REMAINS in the record: a document that failed once and "
          "then worked is a different fact from one that always worked",
          str(len(after["attempts"])))
    check(len({a["batch_id"] for a in after["attempts"]}) == 2,
          "and the retry is its own batch of one, which is what makes per-document retry "
          "visible in the record")
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PRJ))
        attempt_rows = s.scalars(select(UploadAttempt).where(
            UploadAttempt.project_id == proj.id)).all()
    check(all(a.error is None for a in attempt_rows if a.status != "failed"),
          "a successful attempt carries no error text")
    check(all(a.error for a in attempt_rows if a.status == "failed"),
          "and a failed one always carries a reason: the table's own constraint refuses a "
          "failure with none")

    print()
    print("=" * 78)
    print("5. EVERY PERIOD COMPUTES, IN ORDER, and an earlier period stays byte-identical")
    print("=" * 78)

    _COMPARED = ("period", "signal_inputs", "module_results", "category_statuses",
                 "project_status", "portfolio_snapshot", "simulation_version", "seed",
                 "period_cutoff", "source_documents")

    def payload_bytes(period: int) -> bytes:
        with Session() as s:
            proj = s.scalar(select(Project).where(Project.legacy_id == PRJ))
            row = s.scalars(select(ComputedResult).where(
                ComputedResult.project_id == proj.id, ComputedResult.period == period,
                ComputedResult.superseded_by.is_(None))).first()
            assert row is not None, f"no live result for period {period}"
            return json.dumps({k: getattr(row, k) for k in _COMPARED},
                              sort_keys=True, default=str).encode()

    # Captured BEFORE the later periods are computed, and produced before they were uploaded.
    before_p1 = payload_bytes(1)

    all_resp = post({"action": "projectcomputeall", "session_token": pm, "id": PRJ})
    check(all_resp.get("ok") is True, "the all-periods control computes", str(all_resp)[:200])
    check(all_resp["periods"] == [1, 2, 3],
          "every period the project holds documents for, and only those",
          str(all_resp.get("periods")))
    check([r["period"] for r in all_resp["results"]] == sorted(
              r["period"] for r in all_resp["results"]),
          "IN ORDER, oldest first, which is the ordering the byte-identical invariant needs",
          str([r["period"] for r in all_resp["results"]]))
    check(all_resp["computed"] == 2 and all_resp["skipped"] == 1,
          "the two uncomputed periods compute and the one that already had a result is left "
          "untouched", str(all_resp)[:200])
    check(payload_bytes(1) == before_p1,
          "and period 1, computed before periods 2 and 3 existed, is byte-identical after they "
          "were computed: the all-periods run did not disturb it")

    before_p2 = payload_bytes(2)

    # Each period saw only itself and earlier periods. Recomputing period 1 now, with periods 2
    # and 3 both stored, must reproduce the row that was produced when neither existed.
    post({"action": "adminrecompute", "session_token": admin, "id": PRJ, "period": 1,
          "reason": "byte-identical check after the all-periods compute"})
    after_p1 = payload_bytes(1)
    check(after_p1 == before_p1,
          "RECOMPUTING PERIOD 1 AFTER EVERY LATER PERIOD EXISTS IS BYTE-IDENTICAL with the row "
          "computed when period 1 was the only period",
          f"first difference at byte {next((i for i, (a, b) in enumerate(zip(before_p1, after_p1)) if a != b), 'n/a')}")
    check(payload_bytes(2) == before_p2,
          "and period 2 is untouched by the recompute of period 1")

    again = post({"action": "projectcomputeall", "session_token": pm, "id": PRJ})
    check(again.get("ok") is True and again["computed"] == 0 and again["skipped"] == 3,
          "running it a second time computes nothing: a period that already has a live result "
          "is left untouched, because replacing one is an audited, reason-bearing operation",
          str(again)[:200])
    check(payload_bytes(1) == before_p1 and payload_bytes(2) == before_p2,
          "and every stored result is byte-identical after that second run")

    print()
    print("-" * 78)
    print("5b. Refused server-side for a research account. Called directly.")
    print("-" * 78)

    research = post({"action": "adminparticipantcreate", "session_token": admin,
                     "pseudonymous_code": "UNB-RESEARCH", "role": "Participant",
                     "account_type": "research"})
    r_token = post({"action": "researchlogin",
                    "access_token": research["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": admin, "id": PRJ,
          "participant_id": research["participant_id"], "project_role": "PM"})

    refusal = post({"action": "projectcomputeall", "session_token": r_token, "id": PRJ})
    check(refusal.get("ok") is not True,
          "a research account calling projectcomputeall DIRECTLY is refused, whatever any "
          "button does", str(refusal)[:200])
    check("operational" in (refusal.get("error") or ""),
          "and told why, in a sentence about this account rather than a generic denial",
          str(refusal.get("error")))
    check("projectcomputeall" in RESEARCH_FORBIDDEN_ACTIONS,
          "the dispatch-level gate carries it too, so the refusal does not depend on one "
          "function remembering to check")
    check(payload_bytes(1) == before_p1,
          "and the refused call changed nothing that was stored")

    # A PM on an operational account is still allowed, so the refusal is about the ACCOUNT and
    # not about the action being broken.
    check(post({"action": "projectcomputeall", "session_token": pm,
                "id": PRJ}).get("ok") is True,
          "while the operational PM is still allowed: the gate is on the account type")

    print()
    print("=" * 78)
    print("6. Heading mapping, and the tables that are NOT activity tables")
    print("=" * 78)

    check(map_headings(HEADINGS).get("current_finish") == "Actual finish",
          "the real headings map", str(map_headings(HEADINGS)))
    check(map_headings(["Project", "Value", "Issue date", "Data date"]) .get("activity_key")
          is None,
          "a document header block resolves no identity column",
          str(map_headings(["Project", "Value", "Issue date", "Data date"])))
    check(find_activity_table([[["Project", "X"], ["Contract", "Y"], ["Period", "Z"]]]) is None,
          "and a document with only such a table has no activity table, rather than the "
          "nearest thing being guessed at")
    check(find_activity_table([[HEADINGS, activity_row(1, finished=False,
                                                       forecast_finish="01-Apr-26",
                                                       baseline_finish="01-Apr-26")]]) is None,
          "one data row is a summary line, not a list of activities")
    check(activity_table_from_document(b"%PDF-1.4 not a docx", "application/pdf",
                                       "x.pdf") is None,
          "a PDF returns no table rather than a guessed one: its tables are not available on "
          "this side of the model boundary, and that limit is reported rather than worked around")

    print()
    print("=" * 78)
    print("7. The real document, if one was supplied")
    print("=" * 78)

    real_path = (os.environ.get("REAL_SCHEDULE_DOCX") or "").strip()
    if real_path and os.path.exists(real_path):
        with open(real_path, "rb") as fh:
            real_raw = fh.read()
        real_table = activity_table_from_document(real_raw, "", os.path.basename(real_path))
        check(real_table is not None,
              f"the real document's activity table is recognised ({real_path})")
        if real_table is not None:
            real_rows = activity_rows_from_document(real_raw, "", "real.docx")
            check(len(real_rows) == real_table.row_count,
                  f"every one of its {real_table.row_count} rows parses",
                  str(len(real_rows)))
            check(all(r["usable_for_trend"] for r in real_rows),
                  "and every row carries a readable finish date",
                  str([r["activity_key"] for r in real_rows if not r["usable_for_trend"]]))
            rec = Recorder()
            ex = AnthropicExtractor("key-not-used")
            ex._post = rec  # noqa: SLF001
            ex.extract_with_confidence(real_raw, "", "real.docx", "schedule_update")
            check(len(rec.calls) == 1 and "milestones_json" not in rec.calls[0]["prompt"],
                  "one model call, and the table is not asked back from it")
    else:
        print("  ....  REAL_SCHEDULE_DOCX not set; the real-document checks did not run. "
              "The constructed document above reproduces the real extract's shape, not its "
              "contents.")

finally:
    set_extractor_override(None)

print()
print(f"RESULT: {PASSED}/{PASSED + FAILED}")
sys.exit(0 if FAILED == 0 else 1)
