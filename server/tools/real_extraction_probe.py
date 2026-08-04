#!/usr/bin/env python3
"""
Run the REAL extraction model against real document files and report field by field.

Run (from server/):

    ANTHROPIC_API_KEY=... PYTHONIOENCODING=utf-8 python tools/real_extraction_probe.py FILE [FILE...]
    PYTHONIOENCODING=utf-8 python tools/real_extraction_probe.py --make-fixtures DIR

WHY THIS EXISTS

Every verification on this platform to date has run against `StubExtractor` and its recorded
answers. That proves the caching, assembly, guard and storage machinery and proves NOTHING about
what the model actually returns from a document, because the recordings were written by hand.
This tool is the one place the real model is called, so a field-by-field comparison against what
a document actually says can be produced and pasted into a report.

THREE PROPERTIES, ALL DELIBERATE

  * It REFUSES to run without a key, via `build_extractor(require_real=True)`. It must never
    quietly fall back to the stub, because a stub answer printed under the heading "what the
    model returned" is exactly the circular evidence this tool exists to break.
  * It writes NOTHING. No database, no Document row, no observation. It is a probe, not an
    upload; the upload path has its own suite. That also means it is safe to point at a
    production document without touching production state.
  * It runs the SAME guards the upload path runs (`validate_doc_risk_score`,
    `validate_numeric_fields`) and reports a refusal as a refusal, with the value that caused
    it. A guard firing is the guard working and is reported, not suppressed.

`--make-fixtures` writes three synthetic .docx documents whose true values are printed alongside,
so a run against them is a comparison with a known answer rather than an impression. They are
SYNTHETIC and a run against them does not establish behaviour on real project documents; say so
wherever the output is quoted.
"""
from __future__ import annotations

import sys
import zipfile
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

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


def _p(t: str) -> str:
    return f'<w:p><w:r><w:t xml:space="preserve">{escape(t)}</w:t></w:r></w:p>'


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


def _docx(blocks: list[str]) -> bytes:
    doc = (f'<?xml version="1.0" encoding="UTF-8"?><w:document {_NS}><w:body>'
           + "".join(blocks) + "</w:body></w:document>")
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", _CT)
        z.writestr("_rels/.rels", _RELS)
        z.writestr("word/document.xml", doc)
    return buf.getvalue()


# Each fixture carries the TRUTH alongside it, so the comparison is against a stated answer
# rather than against a later reading of the same document.
FIXTURES: dict[str, tuple[bytes, dict]] = {
    "pay_application_07.docx": (_docx([
        _p("APPLICATION AND CERTIFICATE FOR PAYMENT"),
        _p("Project: Terminal C Baggage Handling Upgrade"),
        _p("Application No: 7        Period From: 2026-06-01        Period To: 2026-06-30"),
        _p("Date of Application: 2026-07-05"),
        _tbl([
            ["Item", "Description of Work", "Scheduled Value", "Work Completed This Period",
             "Total Completed and Stored to Date", "% (G/C)", "Balance to Finish"],
            ["01", "General Conditions", "450,000.00", "37,500.00", "337,500.00", "75.0",
             "112,500.00"],
            ["02", "Conveyor Structure", "2,800,000.00", "210,000.00", "1,960,000.00", "70.0",
             "840,000.00"],
            ["03", "Controls and Integration", "1,350,000.00", "94,500.00", "742,500.00",
             "55.0", "607,500.00"],
            [("GRAND TOTAL", 2), "4,600,000.00", "342,000.00", "3,040,000.00", "66.1",
             "1,560,000.00"],
        ]),
        _p("Original Contract Sum: 4,600,000.00"),
        _p("Net change by Change Orders: 0.00"),
        _p("Contract Sum to Date: 4,600,000.00"),
        _p("Total Completed and Stored to Date: 3,040,000.00"),
        _p("Retainage 5%: 152,000.00"),
        _p("Total Earned Less Retainage: 2,888,000.00"),
        _p("Less Previous Certificates for Payment: 2,563,100.00"),
        _p("CURRENT PAYMENT DUE: 324,900.00"),
        _p("Original Contingency: 230,000.00      Remaining Contingency: 184,000.00"),
    ]), {
        "amount_paid_to_date": 2888000.0,
        "percent_complete_verified": 66.1,
        "original_contract_sum": 4600000.0,
        "completed_to_date": 3040000.0,
        "work_period_from": "2026-06-01",
        "work_period_to": "2026-06-30",
        "application_date": "2026-07-05",
        "original_contingency": 230000.0,
        "remaining_contingency": 184000.0,
    }),

    "monthly_earned_value_summary.docx": (_docx([
        _p("MONTHLY PROJECT STATUS REPORT: EARNED VALUE SUMMARY"),
        _p("Project: Terminal C Baggage Handling Upgrade"),
        _p("Report Date: 2026-06-30"),
        _tbl([
            ["Measure", "Symbol", "This Period", "Cumulative to Date"],
            ["Budget at Completion", "BAC", "", "4,600,000.00"],
            ["Planned Value", "PV", "355,000.00", "3,220,000.00"],
            ["Earned Value", "EV", "342,000.00", "3,040,000.00"],
            ["Actual Cost", "AC", "361,000.00", "3,192,000.00"],
        ]),
        _tbl([
            ["Progress", "Planned", "Actual"],
            ["Percent complete", "70.0", "66.1"],
        ]),
        _p("Note: indices are not reproduced in this report; the analytical layer computes "
           "them from the figures above."),
    ]), {
        "earned_value": 3040000.0,
        "actual_cost": 3192000.0,
        "planned_value": 3220000.0,
        "actual_percent_complete": 66.1,
        "planned_percent_complete": 70.0,
        "budget_at_completion": 4600000.0,
        "report_date": "2026-06-30",
        "milestones_json": None,
    }),

    "rfi_log_june.docx": (_docx([
        _p("REQUEST FOR INFORMATION LOG"),
        _p("Project: Terminal C Baggage Handling Upgrade"),
        _p("Log Date: 2026-06-30      Reporting period: 30 days"),
        _tbl([
            ["RFI No.", "Subject", "Date Issued", "Date Answered", "Status", "Days Open"],
            ["RFI-041", "Conveyor anchor detail", "2026-05-02", "2026-05-09", "Closed", "7"],
            ["RFI-042", "Panel schedule conflict", "2026-05-14", "2026-05-30", "Closed", "16"],
            ["RFI-043", "Fire alarm interface", "2026-05-28", "", "Open", "33"],
            ["RFI-044", "Slab penetration size", "2026-06-08", "2026-06-16", "Closed", "8"],
            ["RFI-045", "Baggage scale grounding", "2026-06-19", "", "Open", "11"],
        ]),
        _tbl([
            ["Summary", "Count"],
            ["Total RFIs issued to date", "45"],
            ["Open", "2"],
            ["Answered", "43"],
            ["Overdue (over 14 days open)", "1"],
            ["Average response time (days)", "9.5"],
            ["Oldest open RFI (days)", "33"],
        ]),
    ]), {
        "rfi_total": 45,
        "rfi_open": 2,
        "rfi_answered": 43,
        "rfi_overdue": 1,
        "avg_response_days": 9.5,
        "rfi_period_days": 30,
        "oldest_open_days": 33,
        "log_date": "2026-06-30",
    }),
}

DOCX_MIME = ("application/vnd.openxmlformats-officedocument."
             "wordprocessingml.document")


def make_fixtures(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for name, (raw, truth) in FIXTURES.items():
        (target / name).write_bytes(raw)
        print(f"wrote {target / name}  ({len(raw)} bytes)")
        for k, v in truth.items():
            print(f"    truth  {k:28s} {v!r}")
    print("\nSYNTHETIC documents. A run against these does not establish behaviour on real "
          "project documents.")


def probe(paths: list[str]) -> int:
    from app.extraction_client import ExtractionError, build_extractor
    from app.extraction_fields import extraction_fields_for, is_mapped
    from app.extraction_merge import validate_doc_risk_score, validate_numeric_fields

    try:
        extractor = build_extractor(require_real=True)
    except ExtractionError as exc:
        print(f"REFUSED: {exc}")
        print("This tool never falls back to the stub. Set ANTHROPIC_API_KEY and re-run.")
        return 2
    print(f"extractor: {type(extractor).__name__}  model: "
          f"{getattr(extractor, 'model_id', '?')}\n")

    truths = {name: truth for name, (_raw, truth) in FIXTURES.items()}
    failures = 0
    for path in paths:
        p = Path(path)
        raw = p.read_bytes()
        mime = DOCX_MIME if p.suffix.lower() == ".docx" else (
            "application/pdf" if p.suffix.lower() == ".pdf" else "text/plain")
        print("=" * 78)
        print(f"{p.name}   ({len(raw)} bytes, sent as {mime})")
        print("=" * 78)

        # Report the block the extractor will actually build, because "what was sent" is half
        # of any explanation of what came back.
        try:
            block = extractor._content_block(raw, mime, p.name)
            kind = block["type"]
            size = (len(block.get("text", "")) if kind == "text"
                    else len(block["source"]["data"]))
            print(f"  content block: {kind}  ({size} chars)")
        except Exception as exc:  # noqa: BLE001
            print(f"  content block: COULD NOT BE BUILT: {exc}")
            failures += 1
            continue

        try:
            doc_type, extraction, confidence = extractor.extract_with_confidence(
                raw, mime, p.name, None)
        except ExtractionError as exc:
            print(f"  EXTRACTION FAILED: {exc}")
            failures += 1
            continue

        print(f"  classified as: {doc_type}   confidence: {confidence}")
        if not is_mapped(doc_type):
            print("  (unmapped: no field list applies, nothing was asked for)")
            continue

        truth = truths.get(p.name, {})
        fields = extraction_fields_for(doc_type)
        print(f"\n  {'field':30s} {'model returned':>20s}   {'document says':>20s}   verdict")
        print("  " + "-" * 84)
        for f in fields:
            got = extraction.get(f, "<absent>")
            exp = truth.get(f, "?") if truth else "?"
            if not truth:
                verdict = "-"
            elif got == "<absent>" or got is None:
                verdict = "MISSED" if exp not in (None, "?") else "correctly absent"
            elif exp == "?":
                verdict = "-"
            else:
                try:
                    same = abs(float(got) - float(exp)) < 0.005
                except (TypeError, ValueError):
                    same = str(got).strip() == str(exp).strip()
                verdict = "match" if same else "MISMATCH"
            if verdict in ("MISSED", "MISMATCH"):
                failures += 1
            print(f"  {f:30s} {str(got):>20s}   {str(exp):>20s}   {verdict}")

        extra = sorted(set(extraction) - set(fields))
        if extra:
            print(f"\n  keys outside the declared field list (dropped by the client): {extra}")

        print("\n  guards:")
        for name, fn in (("document risk score range",
                          lambda: validate_doc_risk_score(
                              extraction.get("document_risk_score"), filename=p.name)),
                         ("malformed / out-of-contract numerics",
                          lambda: validate_numeric_fields(doc_type, extraction,
                                                          filename=p.name))):
            try:
                fn()
                print(f"    {name}: passed")
            except Exception as exc:  # noqa: BLE001
                print(f"    {name}: REFUSED -> {exc}")
                failures += 1
        print()

    print("=" * 78)
    print(f"{'NO DISCREPANCIES' if not failures else str(failures) + ' DISCREPANCIES OR REFUSALS'}"
          "  (a refusal may be the guard working; read each one)")
    return 0


def main() -> int:
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 1
    if args[0] == "--make-fixtures":
        make_fixtures(Path(args[1] if len(args) > 1 else "."))
        return 0
    return probe(args)


if __name__ == "__main__":
    sys.exit(main())
