#!/usr/bin/env python3
"""
The risk register read as data, the notice read as an event, and the forecasting modules.

Run (from server/):

    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 \
      python tools/test_risk_register_and_notices.py

Optionally, against the owner's real documents, which are NOT in this repository:

    REAL_RISK_REGISTER=/path/to/Project Risk Register.docx \
    REAL_NOTICE_DOC=/path/to/Consequence Correspondence.docx \
      python tools/test_risk_register_and_notices.py

WHAT THE REAL-DOCUMENT HOOK IS FOR. Two defects on the schedule path were found on real
documents and missed by fixtures, so a fixture-only green here means less than it looks. The
hook is the same one `test_unbounded_schedule.py` uses (`REAL_SCHEDULE_DOCX`): when the variable
is unset the real checks do not run AND SAY SO, rather than passing silently.

THE CENTRAL PROPERTY THIS SUITE HOLDS. A value the register did not state numerically must not
become a number. "High" is not 0.7, a 4-of-5 is not 0.8, and the midpoint of "30-50%" is not 40
per cent. Every one of those is a number imported from outside the document and then presented
as read, which is the precise defect that produced an eightieth-percentile estimate at
completion of 10,555,811 dollars on a project whose authored figure was 4,835,600.
"""
from __future__ import annotations

import os
import sys
import zipfile
from datetime import date
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


# --------------------------------------------------------------------------- docx fixtures
_NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"')
_CT = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/'
       'package/2006/content-types"><Default Extension="xml" ContentType="application/xml"/>'
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
        out.append("<w:tr>" + "".join(f"<w:tc>{_p(c)}</w:tc>" for c in row) + "</w:tr>")
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


# The headings a real register prints, including the unit qualifiers that an exact-match table
# misses. "Schedule Impact (days)" is here on purpose: it resolved to no field at all on the
# first realistic register tried, and every time impact in the table was silently dropped.
REG_HEADINGS = ["Risk ID", "Risk Description", "Risk Category", "Probability (%)",
                "Cost Impact (USD)", "Schedule Impact (days)", "Risk Score", "Risk Owner",
                "Response Strategy", "Mitigation Status", "Residual Risk", "Status"]

# A cover block above the register, so the recogniser has to pass over a table that is NOT the
# register. This is what it does on a real document.
REG_HEADER_BLOCK = _tbl([
    ["Project", "North Concourse Rehabilitation", "", ""],
    ["Document", "Project Risk Register", "Revision", "C"],
    ["Issued", "30 April 2026", "Prepared by", "Risk Manager"],
])


def register_docx(rows: list) -> bytes:
    return _docx([
        _p("PROJECT RISK REGISTER"),
        _p("Revision C - all open and closed risks"),
        REG_HEADER_BLOCK,
        _tbl([REG_HEADINGS] + rows),
        _p("Scores are probability times impact on a 1 to 25 matrix."),
    ])


def register_rows(n: int) -> list:
    """`n` register rows, cycling through the shapes a real register mixes."""
    rows = []
    for i in range(1, n + 1):
        rows.append([
            f"R-{i:03d}", f"Risk event {i}", "Commercial", f"{(i % 9) * 10 + 5}",
            f"${(i % 7 + 1) * 25_000:,}", f"{i % 30}", f"{(i % 5) + 1}",
            f"Owner {i % 4}", "Mitigate", "In progress", "Medium",
            "Open" if i % 3 else "Closed",
        ])
    return rows


def main() -> None:
    from app.risk_register import (
        find_risk_table, map_headings, read_risk_table, risk_rows_from_document,
    )
    from app.risk_values import (
        parse_duration_days, parse_money, parse_open_closed, parse_probability, parse_score,
    )

    section("1. A VALUE THE REGISTER DID NOT STATE NUMERICALLY DOES NOT BECOME A NUMBER")

    # Self-test: the detector for "a probability came back numeric" can distinguish the cases.
    numeric = parse_probability("30%")
    banded = parse_probability("High")
    check(numeric.value == 0.30 and numeric.band is None,
          "self-test: a percentage IS read as a probability", str(numeric))
    check(banded.value is None and banded.band == "High",
          "self-test: a word is NOT read as a probability", str(banded))

    HANDLED = [("30%", 0.30), ("30 %", 0.30), ("30 per cent", 0.30), ("0.3", 0.30),
               (".3", 0.30), ("0", 0.0), ("1", 1.0)]
    for raw, expected in HANDLED:
        got = parse_probability(raw)
        check(getattr(got, "value", None) == expected,
              f"handled as a probability: {raw!r} -> {expected}", str(got))

    REFUSED_AS_NUMBER = ["High", "Very High", "Low", "Remote", "Likely", "4 of 5", "3/5",
                         "Medium (30-50%)"]
    for raw in REFUSED_AS_NUMBER:
        got = parse_probability(raw)
        check(getattr(got, "value", None) is None and getattr(got, "band", None),
              f"recorded as a band, refused as a number: {raw!r}", str(got))

    bare = parse_probability("40")
    check(type(bare).__name__ == "ValueRefusal",
          "a bare number with no unit anywhere REFUSES rather than assuming per cent", str(bare))
    check("ordinal" in getattr(bare, "reason", ""),
          "and the refusal says why: it could be a percentage or an ordinal position",
          getattr(bare, "reason", ""))
    with_col = parse_probability("40", column_is_percent=True)
    check(getattr(with_col, "value", None) == 0.40,
          "the SAME cell reads as 40 per cent when the column heading states the unit",
          str(with_col))

    section("2. MONEY, DURATION AND STATUS: WHAT IS READ AND WHAT REFUSES")

    for raw, expected in [("$120,000", 120000.0), ("120000", 120000.0), ("1.2M", 1200000.0),
                          ("450k", 450000.0), ("(45,000)", -45000.0)]:
        check(parse_money(raw) == expected, f"money handled: {raw!r} -> {expected}",
              str(parse_money(raw)))
    other = parse_money("£90,000")
    check(type(other).__name__ == "ValueRefusal",
          "money in a currency this platform does not convert REFUSES", str(other))

    for raw, expected in [("10 days", 10.0), ("2 weeks", 14.0), ("1 month", 30.0)]:
        check(parse_duration_days(raw) == expected, f"duration handled: {raw!r} -> {expected}")
    check(type(parse_duration_days("14")).__name__ == "ValueRefusal",
          "a bare duration with no unit REFUSES")
    check(parse_duration_days("14", column_unit="days") == 14.0,
          "and reads when the column heading states the unit")

    check(parse_open_closed("Open") is True and parse_open_closed("Closed") is False,
          "open and closed are read")
    mitigated = parse_open_closed("Mitigated")
    check(type(mitigated).__name__ == "ValueRefusal",
          "'Mitigated' REFUSES: it states treatment, not whether the risk is still carried",
          getattr(mitigated, "reason", "")[:60])

    check(parse_probability("") is None and parse_money("-") is None,
          "a blank cell is EMPTY, not a refusal: the register declined to state a value")

    section("3. THE COLUMN MAPPING IS ONE DECISION PER TABLE, AND SURVIVES UNIT QUALIFIERS")

    cmap = map_headings(REG_HEADINGS)
    for field in ("risk_key", "description", "category", "probability", "cost_impact",
                  "time_impact", "score", "owner", "response_strategy", "mitigation_status",
                  "residual_position", "status"):
        check(field in cmap, f"resolved: {field}", cmap.get(field, "(unresolved)"))
    check(cmap.get("time_impact") == "Schedule Impact (days)",
          "a unit-qualified heading resolves, and keeps its unit for the cell parser",
          cmap.get("time_impact"))
    check(cmap.get("cost_impact") == "Cost Impact (USD)",
          "and a currency-qualified one", cmap.get("cost_impact"))
    # Exact-first: a bare "Cost" column must not steal the exact "Cost Impact" column.
    both = map_headings(["Risk ID", "Cost Impact", "Cost", "Probability"])
    check(both.get("cost_impact") == "Cost Impact",
          "exact match wins over a qualifier match for the same field", str(both))
    check(map_headings(["Name", "Phone", "Email"]) == {} or
          "probability" not in map_headings(["Name", "Phone", "Email"]),
          "a contact list resolves no risk-bearing column")

    section("4. THE ROWS ARE READ FROM THE DOCUMENT, AND REFUSALS ARE KEPT")

    mixed = [
        ["R-001", "Unforeseen ground conditions", "Geotechnical", "35", "$450,000", "30",
         "12", "J. Alvarez", "Mitigate", "Boreholes commissioned", "Medium", "Open"],
        ["R-002", "Utility relocation delayed", "External", "High", "$120,000", "45",
         "16", "M. Chen", "Transfer", "Escalated", "High", "Open"],
        ["R-003", "Asphalt price escalation", "Commercial", "20", "1.2M", "0",
         "8", "R. Patel", "Accept", "Locked pricing", "Low", "Closed"],
        ["R-004", "Design query backlog", "Design", "banana", "$90,000", "2 weeks",
         "", "", "Mitigate", "", "", "Mitigated"],
    ]
    rows = risk_rows_from_document(register_docx(mixed), "", "register.docx")
    check(len(rows) == 4, "four risks read from a real .docx", str(len(rows)))
    by_key = {r["risk_key"]: r for r in rows}

    r1 = by_key["R-001"]
    check(r1["probability"] == 0.35 and r1["cost_impact"] == 450000.0,
          "a numeric row yields a probability and a cost impact", str(r1["probability"]))
    check(r1["time_impact_days"] == 30.0,
          "and its time impact, via the column's stated unit", str(r1["time_impact_days"]))
    check(r1["usable_for_exposure"] is True, "and is usable for exposure")
    check(r1["owner"] == "J. Alvarez" and r1["response_strategy"] == "Mitigate"
          and r1["residual_position"] == "Medium" and r1["is_open"] is True,
          "with owner, response, residual position and open status", str(r1["owner"]))

    r2 = by_key["R-002"]
    check(r2["probability"] is None and r2["probability_band"] == "High",
          "a banded row keeps the band and yields NO probability", str(r2["probability_band"]))
    check(r2["usable_for_exposure"] is False,
          "and is NOT usable for exposure, which is what makes a forecast abstain honestly")

    r4 = by_key["R-004"]
    check(r4["unparsed"] and {u["field"] for u in r4["unparsed"]} == {"probability", "status"},
          "a row with unreadable cells is STILL STORED, with the fields that refused named",
          str([(u["field"], u["raw"]) for u in (r4["unparsed"] or [])]))
    check(any(u["raw"] == "banana" for u in r4["unparsed"]),
          "and the refusal names the cell that could not be read")

    check(all(r["risk_key"].startswith("R-") for r in rows),
          "the register's own identifiers are the keys")
    unkeyed = read_risk_table([
        {"Risk Description": "A", "Probability": "10%"},
        {"Risk Description": "B", "Probability": "20%"},
    ])
    check([r["risk_key"] for r in unkeyed] == ["row-1", "row-2"]
          and all(r["keyed_by_position"] for r in unkeyed),
          "a register with no id column is keyed by position, and says so", str(unkeyed[0]))

    section("5. FIVE HUNDRED RISKS COST THE SAME MODEL CALL AS TWENTY")

    from app.risk_register import risk_table_from_document

    small_doc, big_doc = register_docx(register_rows(20)), register_docx(register_rows(500))
    small_t = risk_table_from_document(small_doc, "", "r.docx")
    big_t = risk_table_from_document(big_doc, "", "r.docx")
    check(small_t.row_count == 20 and big_t.row_count == 500,
          "both registers are recognised in full",
          f"{small_t.row_count} and {big_t.row_count}")

    from app.docx_text import docx_to_text

    small_prompt = docx_to_text(small_doc, {small_t.index: small_t.elision_note()})
    big_prompt = docx_to_text(big_doc, {big_t.index: big_t.elision_note()})
    # Self-test: WITHOUT elision the two differ enormously, so the equality below is not vacuous.
    check(len(docx_to_text(big_doc)) > 10 * len(docx_to_text(small_doc)),
          "self-test: un-elided, a 500-row register is far larger than a 20-row one",
          f"{len(docx_to_text(small_doc))} vs {len(docx_to_text(big_doc))}")
    delta = abs(len(big_prompt) - len(small_prompt))
    check(delta <= 2,
          "elided, the text sent to the model differs by at most the row-count digits",
          f"{len(small_prompt)} vs {len(big_prompt)} chars, delta {delta}")
    check("must not be returned in your answer" in big_prompt,
          "and the note says the rows were read and must not be returned")
    check("Risk ID" in big_prompt and "R-500" not in big_prompt,
          "the header row survives; no data row is sent")

    big_rows = risk_rows_from_document(big_doc, "", "r.docx")
    check(len(big_rows) == 500, "and all five hundred rows are read", str(len(big_rows)))

    section("6. NO REGISTER, NO GUESS")

    check(risk_rows_from_document(b"not a docx", "", "x.pdf") == [],
          "a PDF yields no rows rather than a guessed layout")
    check(find_risk_table([[["Name", "Phone"], ["a", "b"], ["c", "d"]]]) is None,
          "a two-column contact list is not a risk register")
    check(find_risk_table([[REG_HEADINGS, register_rows(1)[0]]]) is None,
          "a header plus ONE row is a summary line, not a register")

    section("7. THE THREE FORECASTING MODULES: WHAT THEY READ TODAY")

    # This section does NOT change any module. It PINS what each one actually consumes, so the
    # report's claims are checked rather than asserted, and so a later change to any of the
    # three turns this red instead of passing quietly.
    from app.simulation.models import run_rcf
    from app.simulation.models_ext import run_cost_risk, run_parametric_cost
    from app.simulation.rng import pctile

    SI = {"bac": 5_874_620.0, "cpi": 0.673, "ac": 3_000_000.0, "ev": 2_019_000.0,
          "actualPctComplete": 34.0}

    cra = run_cost_risk(dict(SI), lambda: 0.5, date(2026, 4, 30))
    check(cra.get("p80_eac") is not None, "Cost Risk Analysis computes today", str(cra.get("p80_eac")))
    # The reported defect, reproduced from the stated inputs.
    check(cra["p80_eac"] == 10_555_811 and cra["p80_delta_pct"] == 79.7,
          "and reproduces the reported figure exactly: 10,555,811 at 79.7 per cent over budget",
          f"{cra['p80_eac']} / {cra['p80_delta_pct']}")
    # The register plays no part in it: the same inputs with risks attached give the same answer.
    with_risks = dict(SI)
    with_risks["risks"] = [{"probability": 0.35, "cost_impact": 450000.0}] * 20
    again = run_cost_risk(with_risks, lambda: 0.5, date(2026, 4, 30))
    check(again["p80_eac"] == cra["p80_eac"],
          "serving the register changes NOTHING in its answer: it has no slot for the data",
          f"{again['p80_eac']} == {cra['p80_eac']}")

    ordered = sorted([1.00, 1.04, 1.10, 1.14, 1.15, 1.26, 1.38, 1.45, 1.52])
    check(pctile(ordered, 0.80) == 1.38 and pctile(ordered, 0.50) == 1.15,
          "Reference Class Forecasting's percentiles are fixed literals", "1.15 / 1.38")
    rcf_a = run_rcf({"bac": 1_000_000.0}, lambda: 0.5, date(2026, 4, 30))
    rcf_b = run_rcf({"bac": 9_000_000.0}, lambda: 0.5, date(2026, 4, 30))
    check(rcf_a["vs_bac_pct"] == rcf_b["vs_bac_pct"] == 38.0,
          "so its overrun is +38 per cent on EVERY project, whatever the inputs",
          f"{rcf_a['vs_bac_pct']} and {rcf_b['vs_bac_pct']}")
    rcf_none = run_rcf({}, lambda: 0.5, date(2026, 4, 30))
    check(rcf_none.get("status_color") is not None,
          "and with NO budget at all it still returns a colour rather than abstaining",
          str(rcf_none.get("status_color")))

    pc = run_parametric_cost(dict(SI), lambda: 0.5, date(2026, 4, 30))
    check(pc.get("parametric_index") is not None, "Parametric Cost computes today",
          str(pc.get("parametric_index")))
    # Its inputs are all real extracted figures; change one and the answer moves. That is what
    # distinguishes it from the other two and it is asserted, not claimed.
    moved = dict(SI)
    moved["ac"] = SI["ac"] * 1.2
    pc2 = run_parametric_cost(moved, lambda: 0.5, date(2026, 4, 30))
    check(pc2["parametric_index"] != pc["parametric_index"],
          "and its answer MOVES with a real extracted figure, unlike a literal prior",
          f"{pc['parametric_index']} -> {pc2['parametric_index']}")
    check(run_parametric_cost({"bac": 1.0}, lambda: 0.5, date(2026, 4, 30))
          .get("insufficient_data") is True,
          "and it already abstains when its inputs are absent")

    section("8. THE REGISTER IS SERVED TO THE MODULES, IN THE SHAPE A MODULE WOULD READ")

    from app.risk_exposure import register_exposure

    usable = [
        {"risk_key": "R-001", "probability": 0.35, "cost_impact": 450000.0,
         "usable_for_exposure": True, "is_open": True},
        {"risk_key": "R-003", "probability": 0.20, "cost_impact": 1200000.0,
         "usable_for_exposure": True, "is_open": True},
    ]
    banded_only = [
        {"risk_key": "R-002", "probability": None, "probability_band": "High",
         "cost_impact": 120000.0, "usable_for_exposure": False, "is_open": True},
    ]
    exp = register_exposure(usable)
    check(exp["usable_count"] == 2 and exp["risk_count"] == 2,
          "an exposure input is built from the rows that carry both numbers", str(exp))
    check(abs(exp["expected_value"] - (0.35 * 450000 + 0.20 * 1200000)) < 1e-6,
          "its expected value is the sum of probability times impact, and nothing else",
          str(exp["expected_value"]))
    none_exp = register_exposure(banded_only)
    check(none_exp["usable_count"] == 0 and none_exp["expected_value"] is None,
          "a register scored only in bands yields NO exposure input at all", str(none_exp))
    check(none_exp["refused"] and "band" in none_exp["refused"][0]["reason"].lower(),
          "and says why, naming the risk", str(none_exp.get("refused")))
    check(register_exposure([])["usable_count"] == 0,
          "no register at all yields no exposure input")

    section("9. END TO END, OVER HTTP: THE REGISTER AND THE NOTICE REACH THE CARD")

    import base64
    import hashlib
    import json as _json

    from fastapi.testclient import TestClient
    from sqlalchemy import select

    import app.main as main
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor
    from app.models import Project
    from app.research_identity import hash_access_token
    from app.research_models import ComputedResult, Participant, ProjectNotice, ProjectRisk

    client = TestClient(main.app, raise_server_exceptions=False)
    Session = main.SessionFactory
    ADMIN, PRJ = "rrn-admin", "PRJ-RRN"

    REGISTER_DOC = register_docx(mixed)
    NOTICE_TEXT = _docx([
        _p("NOTICE OF CLAIM"),
        _p("From: A Contractor, LLC   To: North Concourse Authority"),
        _p("Served 18 April 2026 by certified mail."),
        _p("Pursuant to AIA Document A201-2017 Section 15.1.3.1, the Contractor gives notice of "
           "a claim for additional compensation and an extension of time arising from the "
           "differing site condition encountered at the apron slab."),
        _p("Reference: RFI 214 and Risk R-001 of the Project Risk Register."),
    ])
    MONTHLY = b"%PDF-1.4 RRN monthly\n"

    REC = {
        hashlib.sha256(REGISTER_DOC).hexdigest(): ("risk_register", {
            "document_risk_score": 0.55, "document_date": "2026-04-30"}),
        hashlib.sha256(NOTICE_TEXT).hexdigest(): ("correspondence_notice", {
            "document_risk_score": 0.71, "document_date": "2026-04-18",
            "notice_served_by": "A Contractor, LLC",
            "notice_served_on": "North Concourse Authority",
            "notice_claim": "additional compensation and an extension of time for a differing "
                            "site condition at the apron slab",
            "notice_date_served": "18-Apr-2026",
            "notice_contract_form": "AIA Document A201-2017",
            "notice_kind": "notice of claim for a differing site condition",
            "notice_references": "RFI 214 and Risk R-001"}),
        hashlib.sha256(MONTHLY).hexdigest(): ("monthly_report", {
            "earned_value": 2.019e6, "actual_cost": 3.0e6, "planned_value": 2.4e6,
            "budget_at_completion": 5.87462e6, "report_date": "2026-04-15",
            "document_date": "2026-04-15"}),
    }
    set_extractor_override(StubExtractor(REC))

    def post(payload: dict) -> dict:
        r = client.post("/exec", content=_json.dumps(payload),
                        headers={"Content-Type": "text/plain"})
        return r.json()

    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="RRNA", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == PRJ)) is None:
            s.add(Project(legacy_id=PRJ, doc={"id": PRJ, "name": "Register drive",
                                              "signals": {}, "events": []}))
        s.commit()

    atok = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    made = post({"action": "adminparticipantcreate", "session_token": atok,
                 "pseudonymous_code": "RRNPM", "role": "Participant",
                 "account_type": "operational"})
    pm = post({"action": "researchlogin", "access_token": made["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": atok, "id": PRJ,
          "participant_id": made["participant_id"], "project_role": "PM"})

    def b64(raw: bytes) -> str:
        return base64.b64encode(raw).decode()

    up = post({"action": "projectupload", "session_token": pm, "id": PRJ, "period": 1,
               "period_end": "2026-04-30", "documents": [
                   {"filename": "Monthly.pdf", "mimeType": "application/pdf",
                    "dataBase64": b64(MONTHLY)},
                   {"filename": "Project Risk Register.docx", "dataBase64": b64(REGISTER_DOC),
                    "mimeType": "application/vnd.openxmlformats-officedocument."
                                "wordprocessingml.document"},
                   {"filename": "Consequence Correspondence.docx", "dataBase64": b64(NOTICE_TEXT),
                    "mimeType": "application/vnd.openxmlformats-officedocument."
                                "wordprocessingml.document"}]})
    check(up.get("ok") is True, "a register and a notice upload", str(up)[:160])

    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PRJ))
        stored = s.scalars(select(ProjectRisk).where(
            ProjectRisk.project_id == proj.id, ProjectRisk.period == 1)).all()
        notices = s.scalars(select(ProjectNotice).where(
            ProjectNotice.project_id == proj.id, ProjectNotice.period == 1)).all()
    check(len(stored) == 4, "four risks are STORED, one row each", str(len(stored)))
    check(sum(1 for r in stored if r.usable_for_exposure) == 2,
          "two of them carry both numbers and are usable for exposure",
          str([(r.risk_key, r.usable_for_exposure) for r in stored]))
    banded = [r for r in stored if r.risk_key == "R-002"][0]
    check(banded.probability is None and banded.probability_band == "High",
          "the banded risk stores its band and NO probability", str(banded.probability_band))
    refused = [r for r in stored if r.risk_key == "R-004"][0]
    check(refused.unparsed and any(u["field"] == "probability" for u in refused.unparsed),
          "the unreadable one stores its refusal, naming the row and the field",
          str(refused.unparsed))

    check(len(notices) == 1, "the notice is stored as one event", str(len(notices)))
    n = notices[0]
    check(n.served_by == "A Contractor, LLC" and n.served_on == "North Concourse Authority",
          "with who served it and on whom", f"{n.served_by} -> {n.served_on}")
    check(n.date_served is not None and n.date_served.isoformat() == "2026-04-18",
          "and the date served, read by the refusing parser", str(n.date_served))
    check(n.contract_form == "A201-2017" and n.notice_kind == "differing_site_condition",
          "and the form it named and what it is a notice of",
          f"{n.contract_form} / {n.notice_kind}")
    # A201 differing site conditions is FOURTEEN days, not the 2007 edition's twenty-one.
    check(n.deadline_date is not None and n.deadline_date.isoformat() == "2026-05-02",
          "and the deadline DERIVED from that form: 14 days from 18 April is 2 May",
          str(n.deadline_date))
    check(n.deadline_days == 14 and "3.7.4" in (n.deadline_citation or ""),
          "citing the clause the period comes from", str(n.deadline_citation))
    check(n.deadline_kind == "deadline", "and marked a deadline, not a lookback")

    check(post({"action": "projectcompute", "session_token": pm, "id": PRJ,
                "period": 1}).get("ok") is True, "the period computes")
    res = post({"action": "projectresults", "session_token": pm, "id": PRJ, "period": 1})
    ev = (res.get("result") or {}).get("document_evidence") or {}

    reg = ev.get("register") or {}
    check(reg.get("open_count") == 3, "the card is told three risks are open",
          str(reg.get("open_count")))
    named = reg.get("named") or []
    check(named and any("R-002" in f["sentence"] for f in named),
          "and the card NAMES a risk it read", str([f["sentence"][:44] for f in named]))
    top = [f for f in named if "R-002" in f["sentence"]][0]
    check("High" in top["sentence"],
          "quoting the register's own band rather than a number invented from it",
          top["sentence"][:110])
    check("M. Chen" in top["sentence"] and "Transfer" in top["sentence"],
          "and its named owner and response strategy", top["sentence"][-70:])
    check(not any("0.7" in f["sentence"] or "0.8" in f["sentence"] for f in named),
          "and NO band anywhere became a number", str([f["sentence"] for f in named]))

    nf = ev.get("notices") or []
    check(len(nf) == 1, "the notice reaches the card", str(len(nf)))
    check("A Contractor, LLC served notice on North Concourse Authority" in nf[0]["sentence"],
          "with who served it and on whom", nf[0]["sentence"][:80])
    check("2026-05-02" in nf[0]["clock"] and "3.7.4" in nf[0]["clock"],
          "and the clock it started, with the clause behind it", nf[0]["clock"])

    # The exposure is SERVED into the stored signal inputs, which is what makes the
    # byte-identical check below a real test of it rather than a test of an absent key.
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PRJ))
        row = s.scalars(select(ComputedResult).where(
            ComputedResult.project_id == proj.id, ComputedResult.period == 1,
            ComputedResult.superseded_by.is_(None))).first()
    served = (row.signal_inputs or {}).get("registerExposure")
    check(isinstance(served, dict) and served.get("usable_count") == 1,
          "the register's exposure is SERVED into the analytical layer's inputs", str(served)[:90])
    # R-001 only. R-003 carries both numbers and is CLOSED, so it is stored as usable and
    # excluded from the live exposure: a closed risk is not a live exposure. R-002 is open and
    # banded, so it contributes nothing and is named in `refused`.
    check(abs(served["expected_value"] - (0.35 * 450000)) < 1e-6,
          "carrying the sum the register implies over its OPEN, numeric risks only",
          str(served["expected_value"]))
    check(any(r["risk_key"] == "R-002" for r in served["refused"]),
          "and naming the open risk it could not use, with the reason",
          str(served["refused"]))

    section("10. THE P1 INVARIANT: AN EARLIER PERIOD RECOMPUTES BYTE-IDENTICAL")

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
            return _json.dumps({k: getattr(row, k) for k in _COMPARED},
                               sort_keys=True, default=str).encode()

    before_p1 = payload_bytes(1)

    # A LATER PERIOD WITH ITS OWN, DIFFERENT REGISTER. If period 1's rows could be reached by a
    # later period's register, this is what would move them.
    later_rows = [
        ["R-001", "Unforeseen ground conditions", "Geotechnical", "80", "$999,000", "60",
         "25", "Someone Else", "Escalate", "Reopened", "High", "Open"],
        ["R-009", "A risk that did not exist in period one", "New", "50", "$10,000", "1",
         "5", "New Owner", "Mitigate", "", "Low", "Open"],
        ["R-010", "Another new one", "New", "10", "$1,000", "1", "1", "X", "Accept", "", "", "Open"],
    ]
    LATER_REG = register_docx(later_rows)
    REC[hashlib.sha256(LATER_REG).hexdigest()] = ("risk_register", {
        "document_risk_score": 0.6, "document_date": "2026-05-31"})
    set_extractor_override(StubExtractor(REC))
    post({"action": "projectupload", "session_token": pm, "id": PRJ, "period": 2,
          "period_end": "2026-05-31",
          "documents": [{"filename": "Project Risk Register Rev D.docx",
                         "dataBase64": b64(LATER_REG),
                         "mimeType": "application/vnd.openxmlformats-officedocument."
                                     "wordprocessingml.document"}]})
    check(post({"action": "projectcompute", "session_token": pm, "id": PRJ,
                "period": 2}).get("ok") is True, "a later period with its own register computes")

    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PRJ))
        p1_rows = s.scalars(select(ProjectRisk).where(
            ProjectRisk.project_id == proj.id, ProjectRisk.period == 1)).all()
        p2_rows = s.scalars(select(ProjectRisk).where(
            ProjectRisk.project_id == proj.id, ProjectRisk.period == 2)).all()
    check(len(p1_rows) == 4 and len(p2_rows) == 3,
          "each period holds its own account of the register, not a merged one",
          f"period 1: {len(p1_rows)}, period 2: {len(p2_rows)}")
    p1_r001 = [r for r in p1_rows if r.risk_key == "R-001"][0]
    p2_r001 = [r for r in p2_rows if r.risk_key == "R-001"][0]
    check(p1_r001.probability == 0.35 and p2_r001.probability == 0.80,
          "the SAME risk in two periods is two rows with the two periods' own values",
          f"{p1_r001.probability} then {p2_r001.probability}")

    post({"action": "adminrecompute", "session_token": atok, "id": PRJ, "period": 1,
          "reason": "P1 invariant check after a later period's register arrived"})
    check(payload_bytes(1) == before_p1,
          "RECOMPUTING PERIOD 1 AFTER A LATER PERIOD'S REGISTER EXISTS IS BYTE-IDENTICAL")
    with Session() as s:
        proj = s.scalar(select(Project).where(Project.legacy_id == PRJ))
        again = s.scalars(select(ProjectRisk).where(
            ProjectRisk.project_id == proj.id, ProjectRisk.period == 1)).all()
    check(len(again) == 4,
          "and the recompute inserted no duplicate risk rows", str(len(again)))
    res1 = post({"action": "projectresults", "session_token": pm, "id": PRJ, "period": 1})
    ev1 = (res1.get("result") or {}).get("document_evidence") or {}
    check((ev1.get("register") or {}).get("open_count") == 3,
          "and period 1's card still reports period 1's register, not period 2's",
          str((ev1.get("register") or {}).get("open_count")))

    section("11. THE REAL DOCUMENTS, IF THEY WERE SUPPLIED")

    real_reg = (os.environ.get("REAL_RISK_REGISTER") or "").strip()
    real_notice = (os.environ.get("REAL_NOTICE_DOC") or "").strip()
    if real_reg:
        raw = open(real_reg, "rb").read()
        t = risk_table_from_document(raw, "", os.path.basename(real_reg))
        check(t is not None, f"the real register is recognised: {os.path.basename(real_reg)}",
              "no register table found" if t is None else f"{t.row_count} rows")
        if t is not None:
            real_rows = risk_rows_from_document(raw, "", os.path.basename(real_reg))
            print(f"    column map: {t.column_map}")
            print(f"    rows: {len(real_rows)}  usable for exposure: "
                  f"{sum(1 for r in real_rows if r['usable_for_exposure'])}")
            refusals = [(r["risk_key"], u["field"], u["raw"])
                        for r in real_rows for u in (r["unparsed"] or [])]
            print(f"    refusals: {len(refusals)}  {refusals[:8]}")
            check(len(real_rows) == t.row_count,
                  "every data row in the real register is read", f"{len(real_rows)}")
            check(all(r["probability"] is None or 0.0 <= r["probability"] <= 1.0
                      for r in real_rows),
                  "and no probability read from it is outside 0 to 1")
    else:
        print("  ....  REAL_RISK_REGISTER not set; the real-register checks did not run. "
              "Set it to the owner's Project Risk Register and re-run.")
    if real_notice:
        raw = open(real_notice, "rb").read()
        from app.docx_text import docx_to_text
        from app.contract_notices import identify_form, identify_notice_type
        text = docx_to_text(raw)
        print(f"    named form: {identify_form(text)}   kind: {identify_notice_type(text)}")
        check(True, f"the real notice was read: {os.path.basename(real_notice)}",
              f"{len(text)} chars")
    else:
        print("  ....  REAL_NOTICE_DOC not set; the real-notice checks did not run. "
              "Set it to the owner's Consequence Correspondence document and re-run.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — a crash must print a FAILING result line
        import traceback
        traceback.print_exc()
        check(False, f"suite crashed: {type(exc).__name__}: {exc}")
    finish()
