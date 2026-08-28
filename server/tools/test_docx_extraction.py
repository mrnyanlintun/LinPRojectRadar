#!/usr/bin/env python3
"""
Real extraction: the docx reader, the format split, and the wired `extractsignals` action.

Run (from server/):

    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_docx_extraction.py

WHAT THIS COVERS, AND WHAT IT DELIBERATELY CANNOT

The model call itself is NOT exercised: `ANTHROPIC_API_KEY` is absent in local verification and
the stub is the default without it, which section 4 asserts is still true. What IS exercised is
everything on this side of the network boundary, which is where the docx defect lived:

  1. The docx reader, against .docx fixtures built with stdlib only (no python-docx, which is
     not in requirements.txt and not in the server virtualenv).
  2. THE CONTENT BLOCK THE REAL EXTRACTOR WOULD SEND. `AnthropicExtractor._post` is replaced with
     a capture, so the real `extract_with_confidence` runs for real and the block it built is
     asserted. This is the check that would have caught the original defect: it fails if a docx
     goes as binary, and it fails if a PDF stops going as a document block.
  3. `extractsignals` dispatched end to end over /exec, docx and pdf, through the stub.
  4. The stub is still the default without a key.
  5. A malformed numeric refuses through the docx path, naming the field.

Fixtures are built by `_docx()` below rather than checked in as binaries, so a reviewer can read
what the document contains instead of taking a blob on trust.
"""
from __future__ import annotations

import base64
import hashlib
import sys
import zipfile
from io import BytesIO
from xml.sax.saxutils import escape

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


# --------------------------------------------------------------------------- fixtures

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
    return f'<w:p><w:r><w:t xml:space="preserve">{escape(text)}</w:t></w:r></w:p>'


def _deleted(text: str) -> str:
    """Tracked deletion: text struck from the document, which must NOT read as current."""
    return (f'<w:p><w:del w:id="9" w:author="a"><w:r>'
            f'<w:delText xml:space="preserve">{escape(text)}</w:delText></w:r></w:del></w:p>')


def _tbl(rows: list[list]) -> str:
    out = []
    for row in rows:
        cells = []
        for c in row:
            text, span = (c if isinstance(c, tuple) else (c, 1))
            pr = f'<w:tcPr><w:gridSpan w:val="{span}"/></w:tcPr>' if span > 1 else ""
            cells.append(f"<w:tc>{pr}{_p(text)}</w:tc>")
        out.append("<w:tr>" + "".join(cells) + "</w:tr>")
    return "<w:tbl>" + "".join(out) + "</w:tbl>"


def _docx(blocks: list[str], *, main_part: str = "word/document.xml") -> bytes:
    doc = (f'<?xml version="1.0" encoding="UTF-8"?><w:document {_NS}><w:body>'
           + "".join(blocks) + "</w:body></w:document>")
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CT)
        z.writestr("_rels/.rels", _RELS)
        z.writestr(main_part, doc)
    return buf.getvalue()


# A pay application: the format the brief names as the one that matters, carrying its figures in
# a table whose columns are the meaning. The GRAND TOTAL row's first cell spans two grid columns,
# which is what real AIA G702/G703 continuation sheets do.
PAY_APP = _docx([
    _p("APPLICATION AND CERTIFICATE FOR PAYMENT"),
    _p("Application No: 7    Period To: 2026-06-30"),
    _tbl([
        ["Item", "Description of Work", "Scheduled Value", "Work Completed This Period",
         "Total Completed and Stored to Date", "% (G/C)", "Balance to Finish"],
        ["01", "General Conditions", "450,000.00", "37,500.00", "337,500.00", "75.0",
         "112,500.00"],
        ["02", "Conveyor Structure", "2,800,000.00", "210,000.00", "1,960,000.00", "70.0",
         "840,000.00"],
        [("GRAND TOTAL", 2), "4,600,000.00", "342,000.00", "3,040,000.00", "66.1",
         "1,560,000.00"],
    ]),
    _p("Original Contract Sum: 4,600,000.00"),
    _deleted("Total Completed and Stored to Date: 9,999,999.00"),
])

MINIMAL_DOCX = _docx([_p("Monthly report. Earned value 5,000,000.")])

# A real PDF header, so the PDF branch is chosen by content rather than by the caller's word.
PDF_BYTES = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n%%EOF\n"


def main() -> None:
    from fastapi.testclient import TestClient
    from sqlalchemy import select

    import app.main as main_mod
    from app.documents import set_extractor_override
    from app.docx_text import (
        DOCX_TEXT_LIMIT, TRUNCATION_NOTE, DocxReadError, docx_content_block, docx_to_text,
        is_docx,
    )
    from app.extraction_client import (
        AnthropicExtractor, ExtractionError, StubExtractor, build_extractor,
    )
    from app.research_identity import hash_access_token
    from app.research_models import Document, Observation, Participant
    from app.models import Project
    import os

    # ---------------------------------------------------------------- 1. the reader
    section("1. THE DOCX READER: TEXT, AND TABLES THAT KEEP THEIR COLUMNS")

    text = docx_to_text(PAY_APP)
    check("APPLICATION AND CERTIFICATE FOR PAYMENT" in text,
          "body prose is read", text[:60])
    check(text.count("�") == 0,
          "no replacement characters: the archive is parsed, not decoded as bytes",
          f"U+FFFD={text.count(chr(0xFFFD))}")

    header_line = next((ln for ln in text.splitlines()
                        if ln.startswith("| Item |")), "")
    check("Total Completed and Stored to Date" in header_line,
          "the table's COLUMN HEADERS survive as a header row", header_line[:70])

    total_line = next((ln for ln in text.splitlines() if "GRAND TOTAL" in ln), "")
    cols = [c.strip() for c in total_line.strip().strip("|").split("|")]
    head_cols = [c.strip() for c in header_line.strip().strip("|").split("|")]
    check(len(cols) == len(head_cols),
          "the merged GRAND TOTAL row has the SAME column count as the header",
          f"{len(cols)} vs {len(head_cols)}")
    # The load-bearing assertion for this whole task: a figure must still sit under its own
    # heading. If gridSpan were not expanded, 4,600,000.00 would land under "Description of
    # Work" and every figure after it would be mislabelled by one column.
    check(head_cols[cols.index("4,600,000.00")] == "Scheduled Value",
          "the grand total sits under 'Scheduled Value', so gridSpan did not shift the row",
          f"under {head_cols[cols.index('4,600,000.00')]!r}"
          if "4,600,000.00" in cols else "value missing")
    check(head_cols[cols.index("3,040,000.00")] == "Total Completed and Stored to Date",
          "and the to-date figure sits under its own heading")

    check("9,999,999.00" not in text,
          "a TRACKED DELETION is not read as current text")

    check(docx_to_text(PAY_APP) == text,
          "the reader is deterministic for identical bytes")

    # ---------------------------------------------------------------- 2. refusals, no fallback
    section("2. UNREADABLE INPUT REFUSES; IT NEVER FALLS BACK TO THE BINARY BRANCH")

    for label, blob in (("not a zip", b"this is plainly not a docx"),
                        ("zip without word/document.xml",
                         _docx([_p("x")], main_part="word/other.xml"))):
        try:
            docx_to_text(blob)
            check(False, f"{label} raises DocxReadError", "no exception")
        except DocxReadError as exc:
            check(True, f"{label} raises DocxReadError", str(exc)[:60])
        except Exception as exc:  # noqa: BLE001
            check(False, f"{label} raises DocxReadError", f"got {type(exc).__name__}")

    try:
        docx_content_block(_docx([_p("   ")]))
        check(False, "an empty docx refuses rather than sending nothing", "no exception")
    except DocxReadError:
        check(True, "an empty docx refuses rather than sending nothing")

    big = _docx([_p("R" + str(i) + " " + "9" * 400) for i in range(400)])
    block = docx_content_block(big)
    check(len(docx_to_text(big)) > DOCX_TEXT_LIMIT, "the oversized fixture really is oversized",
          str(len(docx_to_text(big))))
    check(block["text"].endswith(TRUNCATION_NOTE),
          "truncation is ANNOUNCED in the prompt, never silent")

    # ---------------------------------------------------------------- 3. the format split
    section("3. THE BLOCK THE REAL EXTRACTOR BUILDS, PER FORMAT")

    check(is_docx(PAY_APP, "", "x.docx"), "a docx is recognised from its bytes")
    check(not is_docx(PDF_BYTES, "", "x.pdf"), "a pdf is not mistaken for a docx")
    # signals.js sends `file.type || "application/pdf"`, so this is the live case, not a hypothetical.
    # BOTH the mime type and the extension lie here, so only the bytes can decide. Using a
    # ".docx" filename would let the extension fallback answer and the sniff could be removed
    # without this going red.
    check(is_docx(PAY_APP, "application/pdf", "payapp"),
          "a docx LYING about its mime type AND extension is recognised, because bytes win")

    captured: list[dict] = []

    class CapturingExtractor(AnthropicExtractor):
        """The real extractor with only the socket replaced, so real code builds the block."""

        def _post(self, prompt: str, content_block: dict, max_tokens: int) -> str:
            captured.append({"prompt": prompt, "block": content_block})
            return '{"docType": "pay_application", "confidence": 0.9}'

    ex = CapturingExtractor("not-a-real-key")
    captured.clear()
    ex.classify_with_confidence(PAY_APP, "application/pdf", "payapp.docx")
    blk = captured[0]["block"]
    check(blk["type"] == "text",
          "a docx goes to the model as TEXT, not as a document block", blk["type"])
    check("GRAND TOTAL" in blk["text"] and "| Scheduled Value |" in blk["text"],
          "and the text it sends carries the table grid")
    check(blk["text"].count("�") == 0,
          "the block contains no binary mojibake",
          f"U+FFFD={blk['text'].count(chr(0xFFFD))}")
    check("PK\x03\x04" not in blk["text"],
          "the block does not contain the ZIP local-file header, the original defect's signature")

    captured.clear()
    ex.classify_with_confidence(PDF_BYTES, "application/pdf", "report.pdf")
    pblk = captured[0]["block"]
    check(pblk["type"] == "document" and pblk["source"]["media_type"] == "application/pdf",
          "A PDF STILL GOES AS A DOCUMENT BLOCK", pblk["type"])
    check(base64.b64decode(pblk["source"]["data"]) == PDF_BYTES,
          "and carries the original bytes unaltered")

    captured.clear()
    ex.classify_with_confidence(b"plain text report, EV 5000000", "text/plain", "r.txt")
    tblk = captured[0]["block"]
    check(tblk["type"] == "text" and tblk["text"].startswith("DOCUMENT TEXT:\n"),
          "a plain text file still uses the original text branch, unchanged")

    # ---------------------------------------------------------------- 4. the stub default
    section("4. THE STUB IS STILL THE DEFAULT WITHOUT A KEY")

    had_key = bool((os.environ.get("ANTHROPIC_API_KEY") or "").strip())
    check(not had_key, "no ANTHROPIC_API_KEY in this environment (the premise of this section)",
          "set" if had_key else "unset")
    built = build_extractor()
    check(isinstance(built, StubExtractor),
          "build_extractor() returns the STUB when no key is present",
          type(built).__name__)
    check(getattr(built, "model_id", "") == "stub/recorded-v1",
          "and it identifies itself as the stub in the stored model id")
    try:
        build_extractor(require_real=True)
        check(False, "require_real=True still raises without a key", "no exception")
    except ExtractionError as exc:
        check("ANTHROPIC_API_KEY" in str(exc),
              "require_real=True still raises without a key", str(exc)[:50])
    os.environ["ANTHROPIC_API_KEY"] = "sk-test-not-used-for-any-call"
    try:
        real = build_extractor()
        check(isinstance(real, AnthropicExtractor),
              "and returns the REAL extractor when a key IS present",
              type(real).__name__)
    finally:
        del os.environ["ANTHROPIC_API_KEY"]

    # ---------------------------------------------------------------- 5. end to end
    section("5. extractsignals OVER /exec: DOCX AND PDF, THROUGH THE WHOLE PATH")

    import json as _json

    Session = main_mod.SessionFactory
    client = TestClient(main_mod.app)
    PROJ = "DOCX-P-001"
    ADMIN = "docx-admin-token-" + hashlib.sha256(b"docx-suite").hexdigest()[:20]

    def post(body: dict) -> dict:
        r = client.post("/exec", content=_json.dumps(body),
                        headers={"Content-Type": "text/plain"})
        assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
        return r.json()

    with Session() as s:
        row = s.scalar(select(Participant).where(
            Participant.pseudonymous_code == "DOCX-ADMIN"))
        if row is None:
            s.add(Participant(pseudonymous_code="DOCX-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == PROJ)) is None:
            s.add(Project(legacy_id=PROJ,
                          doc={"id": PROJ, "name": "Docx Terminal C", "signals": {}}))
        s.commit()

    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": "DOCX-PM", "role": "Participant",
                    "account_type": "operational"})
    assert created.get("ok"), created
    pm = post({"action": "researchlogin",
               "access_token": created["access_token"]})["session_token"]
    added = post({"action": "adminmemberadd", "session_token": admin, "id": PROJ,
                  "participant_id": created["participant_id"], "project_role": "PM"})
    check(bool(added.get("ok")), "a PM with a project exists to upload into",
          str(added)[:120])

    pay_sha = hashlib.sha256(PAY_APP).hexdigest()
    pdf_sha = hashlib.sha256(PDF_BYTES).hexdigest()
    set_extractor_override(StubExtractor({
        pay_sha: ("pay_application", {"completed_to_date": 3040000.0,
                                     "original_contract_sum": 4600000.0}, 0.93),
        pdf_sha: ("monthly_report", {"earned_value": 5000000.0}, 0.88),
    }))
    try:
        r = post({"action": "extractsignals", "session_token": pm, "id": PROJ, "docType": "auto",
                  "fileName": "pay_app_07.docx",
                  "mimeType": "application/pdf",   # the browser's wrong guess, on purpose
                  "dataBase64": base64.b64encode(PAY_APP).decode("ascii")})
        check(bool(r.get("ok")), "A DOCX UPLOADS AND EXTRACTS through extractsignals",
              str(r)[:160])
        check(r.get("docType") == "pay_application",
              "and the response echoes the document type the legacy panel reads",
              str(r.get("docType")))
        check(sorted(r.get("applied") or []) == ["completed_to_date",
                                                 "original_contract_sum"],
              "`applied` names the fields that were actually stored",
              str(r.get("applied")))

        r2 = post({"action": "extractsignals", "session_token": pm, "id": PROJ, "docType": "auto",
                   "fileName": "monthly.pdf", "mimeType": "application/pdf",
                   "dataBase64": base64.b64encode(PDF_BYTES).decode("ascii")})
        check(bool(r2.get("ok")), "A PDF STILL UPLOADS AND EXTRACTS", str(r2)[:160])
        check(r2.get("docType") == "monthly_report", "and keeps its own type",
              str(r2.get("docType")))

        with Session() as s:
            stored = s.scalars(select(Document).where(Document.sha256 == pay_sha)).first()
            check(stored is not None and stored.doc_type == "pay_application",
                  "the docx is STORED, so the upload was not merely reported")
            check(stored is not None
                  and (stored.extraction or {}).get("original_contract_sum") == 4600000.0,
                  "with the extracted figures on the row")

        # The cache is shared with projectupload because there is only one path.
        r3 = post({"action": "extractsignals", "session_token": pm, "id": PROJ, "docType": "auto",
                   "fileName": "pay_app_07_again.docx", "mimeType": "",
                   "dataBase64": base64.b64encode(PAY_APP).decode("ascii")})
        check(bool(r3.get("ok")) and r3.get("was_cached") is True,
              "re-uploading the same bytes is served from the content-hash cache",
              str(r3.get("was_cached")))

        # ------------------------------------------------------------ 6. the guard
        # RUN 80, OWNER RULING (order section 3, item 3). This section asserted that the docx
        # path REFUSED the whole document for one unreadable field: "the upload is REFUSED" and
        # "NOTHING WAS STORED for the refused document". The owner overrode that -- "a field
        # that cannot be read is absent, and the rest of the document still contributes" -- and
        # these checks now assert what replaces it, on the same document, through the same path.
        # The half that still has to hold is asserted here as it is at every other entry point:
        # the unreadable field reaches the stored extraction nowhere, and the readable figure
        # beside it survives.
        section("6. AN UNREADABLE NUMERIC IS ABSENT THROUGH THE DOCX PATH, NAMING THE FIELD")

        bad_docx = _docx([_p("Pay application. Completed to date: TBD.")])
        bad_sha = hashlib.sha256(bad_docx).hexdigest()
        set_extractor_override(StubExtractor({
            bad_sha: ("pay_application", {"completed_to_date": "TBD",
                                         "original_contract_sum": 4600000.0}, 0.9),
        }))
        bad = post({"action": "extractsignals", "session_token": pm, "id": PROJ, "docType": "auto",
                    "fileName": "bad_pay_app.docx", "mimeType": "",
                    "dataBase64": base64.b64encode(bad_docx).decode("ascii")})
        check(bool(bad.get("ok")), "the upload is ACCEPTED and the document contributes",
              str(bad)[:160])
        msg = " ".join(bad.get("unreadable_fields") or [])
        check("completed_to_date" in msg,
              "and the notice NAMES THE FIELD", msg[:160])
        check("TBD" in msg, "and quotes the value that caused it", msg[:160])
        with Session() as s:
            left = s.scalars(select(Document).where(Document.sha256 == bad_sha)).first()
            # THE DOCUMENT ROW IS STORED, and its `extraction` blob is the model's OWN answer,
            # kept verbatim as the record of what was read -- 'TBD' included. What must not
            # happen is that the unreadable value becomes a FIGURE, and that is asserted on the
            # observation store, which is what every measure actually reads.
            check(left is not None, "the document IS stored rather than discarded whole",
                  str(left)[:80])
            _obs = [o for o in s.scalars(select(Observation).where(
                Observation.document_id == left.document_id)).all()]
            check(not [o for o in _obs if o.field == "completedToDate"]
                  and any(o.field == "bac" and o.value == 4600000.0 for o in _obs),
                  "no observation carries the unreadable field; the readable figure beside it "
                  "IS stored",
                  str([(o.field, o.value) for o in _obs])[:200])
    finally:
        set_extractor_override(None)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — a crash must print a FAILING result line
        import traceback
        traceback.print_exc()
        check(False, f"suite crashed: {type(exc).__name__}: {exc}")
    finish()
