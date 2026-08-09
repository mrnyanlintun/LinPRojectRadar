#!/usr/bin/env python3
"""
The calendar period picker, and the recommendation reading the period's documents.

Run (from server/):

    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_period_picker_and_evidence.py

TWO CHANGES, ONE SUITE, BECAUSE THEY SHARE A PROPERTY: both replace something the platform
asserted with something it can show. The picker replaces a typed period number with a date the
person actually knows and a number derived from it by a rule that is stated. The card replaces
three constants presented as findings with statements read out of named documents.

WHAT SECTION 6 IS FOR, AND WHY IT IS NOT SOMEWHERE ELSE. `document_evidence` is served on the
research pre-lock read, beside `signal_inputs`, because it is evidence and a participant forms
their preliminary judgment from evidence. That is only safe while it stays evidence: the moment
a sentence in it reads as advice, it leaks the recommendation into the pre-lock window and the
whole pre/post contrast in the study becomes uninterpretable. `test_decision_ui_t4.py`'s prose
scanner does NOT cover this -- measured, not assumed: a deliberately planted "escalate to
management review" inside a findings sentence left that suite green at 73/73, because it scans
the decision-state endpoint and this block is served from `projectresults`. So the check lives
here, it scans every sentence the table can generate rather than the handful a fixture happens
to produce, and section 0 proves it can fail before section 6 trusts it.
"""
from __future__ import annotations

import sys
from datetime import date

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


# The vocabulary a sentence must not contain if it is to stay evidence rather than advice.
# Deliberately the same shape as tools/leak_detector's action markers, restated here because
# this scans GENERATED TEMPLATE TEXT rather than a response body and needs no session.
ADVICE_WORDS = (
    "escalate", "escalation", "investigate", "investigation", "monitor", "monitoring",
    "recommend", "recommended", "recommendation", "should", "must", "advise", "advised",
    "course of action", "you should", "we suggest", "suggest",
)


def scan_for_advice(text: str) -> list[str]:
    lowered = str(text or "").lower()
    return [w for w in ADVICE_WORDS if w in lowered]


def main() -> None:
    from app.document_evidence import (
        NO_RANKING_REASON, _CONTENT_NOT_STORED, _FINDINGS, document_evidence,
    )
    from app.extraction_fields import DOC_TYPES, _EXTRACTION_FIELDS

    section("0. SELF-TESTS: EVERY DETECTOR BELOW IS PROVEN ABLE TO FAIL FIRST")

    check(scan_for_advice("11 requests for information are still open") == [],
          "advice scanner passes a plain statement of fact")
    check("escalate" in scan_for_advice("open items: escalate to management review"),
          "advice scanner CATCHES a planted recommendation",
          str(scan_for_advice("open items: escalate to management review")))
    check(scan_for_advice("you should investigate this") != [],
          "advice scanner catches second-person advice")

    section("1. period_for_end_date: THE RULE, EACH ARM")

    # A fake session/project pair is not enough here: the function reads the project's uploads.
    # A tiny in-memory stand-in for the two queries it makes keeps this section deterministic
    # and lets every arm of the rule be driven cheaply; section 7 then exercises the real
    # function, over HTTP, against a real database, so neither the rule nor its wiring is
    # trusted on the strength of the other.
    import app.documents as D

    class _FakeProject:
        id = "p"
        legacy_id = "PRJ-X"

    def with_periods(pairs: list[tuple[int, date]], highest: int | None = None):
        """Patch the two readers `period_for_end_date` depends on, and restore afterwards."""
        orig_ends, orig_high = D._stated_period_ends, D._highest_period
        D._stated_period_ends = lambda s, p: sorted(pairs)
        D._highest_period = lambda s, p: (highest if highest is not None
                                          else (max([n for n, _ in pairs]) if pairs else 0))
        return orig_ends, orig_high

    def restore(o):
        D._stated_period_ends, D._highest_period = o

    P = _FakeProject()

    o = with_periods([(1, date(2026, 3, 31)), (2, date(2026, 4, 30))])
    try:
        r = D.period_for_end_date(None, P, date(2026, 4, 30))
        check(r["period"] == 2 and r["existing"] is True,
              "an exact match on a stated ending date names that existing period", str(r))
        r = D.period_for_end_date(None, P, date(2026, 3, 31))
        check(r["period"] == 1 and r["existing"] is True,
              "and it matches the right one when several exist", str(r))

        r = D.period_for_end_date(None, P, date(2026, 4, 15))
        check(r["period"] == 2 and r["existing"] is True,
              "a date inside a period's window names that period, not a new one", str(r))
        r = D.period_for_end_date(None, P, date(2026, 3, 1))
        check(r["period"] == 1 and r["existing"] is True,
              "a date inside the FIRST period's window names period 1", str(r))

        r = D.period_for_end_date(None, P, date(2026, 5, 31))
        check(r["period"] == 3 and r["existing"] is False,
              "a date later than every stated ending date opens the NEXT period", str(r))
        check(r["period_end"] == date(2026, 5, 31),
              "and the new period's ending date is the date that was picked", str(r))
        check("2026-05-31" in r["basis"] and "2026-04-30" in r["basis"],
              "the basis names both the picked date and the one it is later than", r["basis"])
    finally:
        restore(o)

    o = with_periods([])
    try:
        r = D.period_for_end_date(None, P, date(2026, 1, 31))
        check(r["period"] == 1 and r["existing"] is False,
              "a project with no periods yet: any date opens period 1", str(r))
    finally:
        restore(o)

    # A project holding documents in a period that carries NO stated ending date. The date
    # cannot be placed inside a window that was never stated, so it opens the next period.
    # Asserted rather than left implicit, because the alternative (silently absorbing it into
    # the numbered period) is the guess this whole change exists to remove.
    o = with_periods([], highest=1)
    try:
        r = D.period_for_end_date(None, P, date(2026, 2, 28))
        check(r["period"] == 2 and r["existing"] is False,
              "a period with documents but no stated ending date is not guessed into", str(r))
    finally:
        restore(o)

    section("2. EVERY BASIS SENTENCE EXPLAINS ITSELF AND NAMES NO MODULE")

    o = with_periods([(1, date(2026, 3, 31))])
    try:
        for d in (date(2026, 3, 31), date(2026, 3, 1), date(2026, 9, 30)):
            r = D.period_for_end_date(None, P, d)
            check(bool(r["basis"]) and str(r["period"]) in r["basis"],
                  f"{d.isoformat()}: the basis states the period it decided", r["basis"])
            check("—" not in r["basis"], f"{d.isoformat()}: no em dash in user-facing text")
    finally:
        restore(o)

    section("3. THE FINDINGS TABLE IS KEYED ON THE REAL EXTRACTION VOCABULARY")

    # Self-test: a fake pair is correctly reported as absent, so the loop below can fail.
    check("made_up_field" not in _EXTRACTION_FIELDS.get("rfi_log", []),
          "self-test: a fake field is correctly absent from the vocabulary")

    bad_types = sorted({s["doc_type"] for s in _FINDINGS if s["doc_type"] not in DOC_TYPES})
    check(not bad_types, "every findings row names a current document type", str(bad_types))
    bad_fields = sorted({f"{s['doc_type']}.{s['field']}" for s in _FINDINGS
                         if s["field"] not in _EXTRACTION_FIELDS.get(s["doc_type"], [])})
    check(not bad_fields,
          "every findings row names a field that type's extraction actually declares",
          str(bad_fields))
    bad_unread = sorted(t for t in _CONTENT_NOT_STORED if t not in DOC_TYPES)
    check(not bad_unread, "every content-not-stored type is a current document type",
          str(bad_unread))
    # And those types really do carry nothing but a risk score and a date, which is the whole
    # justification for saying their content is not established.
    for t in _CONTENT_NOT_STORED:
        fields = set(_EXTRACTION_FIELDS.get(t, []))
        check(fields <= {"document_risk_score", "document_date"},
              f"{t} genuinely stores no content beyond a risk score and a date", str(sorted(fields)))

    section("4. document_evidence: WHAT IT REPORTS AND WHAT IT REFUSES TO")

    docs = [
        {"filename": "RFI Log April.pdf", "doc_type": "rfi_log",
         "extraction": {"rfi_open": 11, "rfi_overdue": 0, "oldest_open_days": 47}},
        {"filename": "Notice.pdf", "doc_type": "correspondence_notice",
         "extraction": {"document_risk_score": 0.7, "document_date": "2026-04-18"}},
        {"filename": "Monthly.pdf", "doc_type": "monthly_report",
         "extraction": {"earned_value": 4000000}},
    ]
    ev = document_evidence(docs)
    sentences = [f["sentence"] for f in ev["findings"]]

    check(len(ev["documents_read"]) == 3,
          "every live document is listed as read, including ones that yield no finding",
          str(len(ev["documents_read"])))
    check(any("11 requests for information are still open" == s for s in sentences),
          "a non-zero count becomes a finding, phrased as a plural", str(sentences))
    check(not any("0 requests" in s for s in sentences),
          "a ZERO count is not a finding", str(sentences))
    check(any("47 days" in s for s in sentences), "a day count is reported", str(sentences))
    check(all(f["filename"] for f in ev["findings"]),
          "every finding names the document it came from")
    check(all(f["value"] == int(f["value"]) for f in ev["findings"]),
          "every finding's value is the whole count that was read")
    check(len(ev["not_established"]) == 1
          and ev["not_established"][0]["filename"] == "Notice.pdf",
          "a document whose content is not stored is reported by name, not omitted",
          str(ev["not_established"]))

    # Singular phrasing, and a float that is a whole number, and one that is not.
    ev1 = document_evidence([{"filename": "R.pdf", "doc_type": "rfi_log",
                              "extraction": {"rfi_open": 1}}])
    check(ev1["findings"][0]["sentence"] == "1 request for information is still open",
          "a count of one is phrased in the singular", ev1["findings"][0]["sentence"])
    evf = document_evidence([{"filename": "R.pdf", "doc_type": "rfi_log",
                              "extraction": {"rfi_open": 3.0}}])
    check(len(evf["findings"]) == 1 and evf["findings"][0]["value"] == 3,
          "a whole-numbered float is read as the count it is")
    evx = document_evidence([{"filename": "R.pdf", "doc_type": "rfi_log",
                              "extraction": {"rfi_open": 2.5}}])
    check(evx["findings"] == [], "a fractional value is NOT reported as a count of anything")
    evn = document_evidence([{"filename": "R.pdf", "doc_type": "rfi_log",
                              "extraction": {"rfi_open": None}}])
    check(evn["findings"] == [], "a null extraction value produces no finding")
    evb = document_evidence([{"filename": "R.pdf", "doc_type": "rfi_log",
                              "extraction": {"rfi_open": True}}])
    check(evb["findings"] == [], "a boolean is not silently counted as one")

    check(document_evidence(None)["findings"] == []
          and document_evidence([])["documents_read"] == [],
          "no documents produces an empty report rather than an error")

    section("5. NO SCORE IS INVENTED, AND THE REFUSAL CARRIES ITS REASON")

    for label, arg in (("with documents", docs), ("with none", [])):
        r = document_evidence(arg)["ranking"]
        check(r["possible"] is False, f"{label}: the card is told it cannot rank")
        check(r["reason"] == NO_RANKING_REASON and len(r["reason"]) > 40,
              f"{label}: and is given the reason, in the words it prints")
    check("same three scores on every project" in NO_RANKING_REASON,
          "the reason states WHY the scores rank nothing, not merely that they do not",
          NO_RANKING_REASON)
    # The one thing this module must never grow: a number of its own devising.
    for f in document_evidence(docs)["findings"]:
        check(str(f["value"]) in f["sentence"],
              "every figure in a sentence is the value read from the document, unaltered",
              f["sentence"])

    section("6. THE EVIDENCE STAYS EVIDENCE: NO SENTENCE READS AS ADVICE")

    # Scanned across every sentence the table CAN generate, at both a singular and a plural
    # count, rather than the few a fixture happens to produce.
    offenders: list[str] = []
    for spec in _FINDINGS:
        for n in (1, 7):
            template = spec["singular"] if n == 1 else spec["plural"]
            s = template.format(n=n)
            hits = scan_for_advice(s)
            if hits:
                offenders.append(f"{spec['doc_type']}.{spec['field']}: {s} -> {hits}")
    check(not offenders,
          "no findings sentence contains recommendation or action vocabulary",
          "; ".join(offenders) if offenders else "")

    for entry in _CONTENT_NOT_STORED.values():
        s = (f"This period contains {entry}. Its content is not stored, so what it says is "
             f"not established here.")
        check(not scan_for_advice(s),
              "no content-not-stored sentence reads as advice", s)

    for spec in _FINDINGS:
        check("—" not in spec["singular"] and "—" not in spec["plural"],
              f"{spec['doc_type']}.{spec['field']}: no em dash in user-facing text")
        check("bearing" in spec and spec["bearing"] and "—" not in spec["bearing"],
              f"{spec['doc_type']}.{spec['field']}: states what it bears on")

    # NAMING_AUTHORITY: no module id or category id anywhere a reader can see.
    import re as _re
    idpat = _re.compile(r"(^|[^A-Za-z0-9])[A-D]\d(\.\d+)?([^A-Za-z0-9]|$)")
    for spec in _FINDINGS:
        for n in (1, 7):
            s = (spec["singular"] if n == 1 else spec["plural"]).format(n=n)
            check(not idpat.search(s), f"no module or category id in: {s[:48]}")
    check(not idpat.search(NO_RANKING_REASON), "no module or category id in the ranking reason")

    section("7. OVER HTTP, AGAINST A REAL DATABASE: THE PREVIEW AND THE UPLOAD AGREE")

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
    from app.research_models import Participant

    client = TestClient(main.app, raise_server_exceptions=False)
    Session = main.SessionFactory
    ADMIN, PRJ = "ppe-admin", "PRJ-PPE"

    def raw(tag: str) -> bytes:
        return f"%PDF-1.4 PPE {tag}\n".encode()

    REC = {
        hashlib.sha256(raw("M1")).hexdigest(): ("monthly_report", {
            "earned_value": 3e6, "actual_cost": 3.3e6, "planned_value": 3.2e6,
            "budget_at_completion": 1.2e7, "report_date": "2026-03-15",
            "document_date": "2026-03-15"}),
        hashlib.sha256(raw("RFI")).hexdigest(): ("rfi_log", {
            "rfi_total": 40, "rfi_open": 9, "rfi_overdue": 2, "oldest_open_days": 31,
            "log_date": "2026-04-30"}),
    }
    set_extractor_override(StubExtractor(REC))

    def post(payload: dict) -> dict:
        r = client.post("/exec", content=_json.dumps(payload),
                        headers={"Content-Type": "text/plain"})
        return r.json()

    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="PPEA", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        if s.scalar(select(Project).where(Project.legacy_id == PRJ)) is None:
            s.add(Project(legacy_id=PRJ, doc={"id": PRJ, "name": "Picker drive",
                                              "signals": {}, "events": []}))
        s.commit()

    atok = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    made = post({"action": "adminparticipantcreate", "session_token": atok,
                 "pseudonymous_code": "PPEPM", "role": "Participant",
                 "account_type": "operational"})
    pm = post({"action": "researchlogin", "access_token": made["access_token"]})["session_token"]
    post({"action": "adminmemberadd", "session_token": atok, "id": PRJ,
          "participant_id": made["participant_id"], "project_role": "PM"})

    # Period 1, stated as ending 2026-03-31.
    up1 = post({"action": "projectupload", "session_token": pm, "id": PRJ, "period": 1,
                "period_end": "2026-03-31",
                "documents": [{"filename": "M1.pdf", "mimeType": "application/pdf",
                               "dataBase64": base64.b64encode(raw("M1")).decode()}]})
    check(up1.get("ok") is True, "a first period is uploaded with a stated ending date")

    prev_same = post({"action": "projectperiodfordate", "session_token": pm, "id": PRJ,
                      "period_end": "2026-03-31"})
    check(prev_same.get("period") == 1 and prev_same.get("existing") is True,
          "the preview resolves that same date to the existing period 1", str(prev_same))
    prev_new = post({"action": "projectperiodfordate", "session_token": pm, "id": PRJ,
                     "period_end": "2026-04-30"})
    check(prev_new.get("period") == 2 and prev_new.get("existing") is False,
          "and a later date to a NEW period 2", str(prev_new))
    check(bool(prev_new.get("basis")), "the preview explains which arm decided",
          str(prev_new.get("basis")))
    bad = post({"action": "projectperiodfordate", "session_token": pm, "id": PRJ,
                "period_end": "not-a-date"})
    check(bad.get("ok") is not True, "an unparseable date is refused, not guessed", str(bad))

    # THE POINT OF THE WHOLE CHANGE: upload stating ONLY the date, no period number, and it
    # must land in exactly the period the preview named.
    up2 = post({"action": "projectupload", "session_token": pm, "id": PRJ,
                "period_end": "2026-04-30",
                "documents": [{"filename": "RFI.pdf", "mimeType": "application/pdf",
                               "dataBase64": base64.b64encode(raw("RFI")).decode()}]})
    check(up2.get("ok") is True, "a document uploads with a date and no period number")
    check(up2.get("period") == prev_new.get("period") == 2,
          "and lands in the period the preview named, with no number ever sent",
          f"upload={up2.get('period')} preview={prev_new.get('period')}")

    st1 = post({"action": "projectuploadstatus", "session_token": pm, "id": PRJ, "period": 1})
    st2 = post({"action": "projectuploadstatus", "session_token": pm, "id": PRJ, "period": 2})
    check(len(st1.get("documents") or []) == 1,
          "period 1 still holds only its own document", str(len(st1.get("documents") or [])))
    check(len(st2.get("documents") or []) == 1,
          "period 2 holds the calendar-filed one", str(len(st2.get("documents") or [])))

    # No date and no number is still period 1: the server-side default is unchanged, and the
    # refusal to upload without a date is the CLIENT's (see signals.js handleFiles). Asserted
    # so a later change to either side cannot quietly diverge from the other.
    check(post({"action": "projectperiodfordate", "session_token": pm,
                "id": PRJ})["ok"] is not True,
          "the preview refuses when no date is supplied at all")

    section("8. AND THE CARD IS SERVED WHAT THE DOCUMENTS SAY, AT DISPLAY TIME")

    check(post({"action": "projectcompute", "session_token": pm, "id": PRJ,
                "period": 2}).get("ok") is True, "period 2 computes")
    res = post({"action": "projectresults", "session_token": pm, "id": PRJ, "period": 2})
    ev2 = (res.get("result") or {}).get("document_evidence")
    check(isinstance(ev2, dict), "projectresults carries document_evidence", str(type(ev2)))
    sents = [f["sentence"] for f in (ev2 or {}).get("findings", [])]
    check(any("9 requests for information are still open" == s for s in sents),
          "a figure read out of the period's own RFI log reaches the card", str(sents))
    names = {f["filename"] for f in (ev2 or {}).get("findings", [])}
    check(names == {"RFI.pdf"}, "and every statement names the document it came from", str(names))
    check((ev2 or {}).get("ranking", {}).get("possible") is False,
          "the card is told it cannot rank, on a real read")

    # Period 1 holds only a monthly report, which carries no readable open items. The card must
    # report nothing rather than borrow period 2's findings.
    check(post({"action": "projectcompute", "session_token": pm, "id": PRJ,
                "period": 1}).get("ok") is True, "period 1 computes too")
    res1 = post({"action": "projectresults", "session_token": pm, "id": PRJ, "period": 1})
    ev1h = (res1.get("result") or {}).get("document_evidence") or {}
    check(ev1h.get("findings") == [],
          "a period whose documents establish nothing reports nothing", str(ev1h.get("findings")))
    check(len(ev1h.get("documents_read") or []) == 1,
          "and still lists the document it read", str(ev1h.get("documents_read")))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # noqa: BLE001 — a crash must print a FAILING result line
        import traceback
        traceback.print_exc()
        check(False, f"suite crashed: {type(exc).__name__}: {exc}")
    finish()
