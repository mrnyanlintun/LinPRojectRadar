#!/usr/bin/env python3
"""
The Files tab: the Arora tree, automatic filing, the two filed states, versions and preview.

Run (from server/):

    DATABASE_URL=... SESSION_SECRET=... PYTHONIOENCODING=utf-8 python tools/test_files_tab.py

Covers, end to end through /exec plus the pure layer:

  1. The tree is the Arora template and NOTHING is materialised per project: a project that has
     filed nothing still gets the template, with every folder unoccupied.
  2. A document of a known type files into the expected folder.
  3. A low-confidence document lands in the reviewable location and is flagged.
  4. A reference corpus document is filed and does NOT enter the analytical path.
  5. A second version appears alongside the first rather than replacing it.
  6. An unsupported format reports itself as unsupported rather than being previewed.
  7. The two identifier-bearing branches are not flattened into a type-then-date rule.
  8. The reference corpus read is gated on the server by the existing feature flag, and filing
     is NOT gated by it.
  9. A misfile can be moved, and moving resolves the review flag.

The whole run is wrapped so a crash prints a failing RESULT line, never a clean-looking silence.
"""
from __future__ import annotations

import base64
import hashlib
import json
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


def main() -> None:
    from fastapi.testclient import TestClient
    from sqlalchemy import select

    import app.main as main_mod
    import app.jdrive_tree as jt
    from app.documents import set_extractor_override
    from app.extraction_client import StubExtractor
    from app.extraction_merge import assemble_signal_inputs
    from app.models import Project
    from app.research_identity import hash_access_token
    from app.research_models import Document, DocumentUpload, Participant

    client = TestClient(main_mod.app, raise_server_exceptions=False)
    Session = main_mod.SessionFactory

    def post(payload: dict) -> dict:
        r = client.post("/exec", content=json.dumps(payload),
                        headers={"Content-Type": "text/plain"})
        assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
        return r.json()

    def b64(raw: bytes) -> str:
        return base64.b64encode(raw).decode()

    def blob(tag: str) -> bytes:
        return f"%PDF-1.4 FILES TAB {tag}\n".encode()

    def sha(raw: bytes) -> str:
        return hashlib.sha256(raw).hexdigest()

    # A recording may carry a third element, the classifier's confidence. That is the value the
    # platform used to discard; the filing threshold reads it.
    FILES = {
        # a known type, high confidence -> its own folder in the template
        "payapp.pdf": ("pay_application",
                       {"amount_paid_to_date": 4_000_000, "application_date": "2026-06-15"},
                       0.95),
        # the same type, LOW confidence -> the reviewable destination
        "maybe.pdf": ("pay_application",
                      {"amount_paid_to_date": 1_000, "application_date": "2026-06-20"}, 0.20),
        # identifier-bearing branches
        "CO-014.pdf": ("change_order",
                       {"revised_contract_sum": 11_000_000,
                        "change_order_date": "2026-06-10"}, 0.9),
        "site obs 3.pdf": ("field_report",
                           {"document_risk_score": 0.4, "document_date": "2026-06-12"}, 0.9),
        # version 1 and version 2 of one register
        "rfilog-v1.pdf": ("rfi_log", {"rfi_total": 10, "log_date": "2026-06-01"}, 0.9),
        "rfilog-v2.pdf": ("rfi_log", {"rfi_total": 12, "log_date": "2026-06-08"}, 0.9),
    }
    RECORDED = {sha(blob(k)): v for k, v in FILES.items()}
    # Documents the analytical classifier IS asked about and cannot map: a Revit model and a
    # spreadsheet. They are filed-class, not reference, so they still go through extraction and
    # legitimately need a recording; both classify UNMAPPED with no confidence, which is what
    # the real classifier would return for them.
    for name in ("Tower.rvt", "notes.xlsx"):
        RECORDED[sha(blob(name))] = ("unmapped", {})
    # THE SPECIFICATION IS DELIBERATELY NOT RECORDED, and that is the check.
    #
    # It used to be, under a comment reading "documents the analytical extractor is never asked
    # about" — the comment stated the intent and the fixture quietly guaranteed the opposite
    # could not be detected. Filing was decided AFTER extraction, so every reference document
    # did go to the extractor, and the recording made that invisible. Same shape as the render
    # harness's primed cache: a fixture that supplies what production cannot.
    #
    # `StubExtractor` REFUSES a hash it has not been given rather than inventing an extraction.
    # So if anything ever routes a specification to the analytical path again, there is no
    # recording to answer with, the upload comes back "failed", and the reference checks below
    # go red. Do not add a recording for it to make a failure go away: the failure IS the
    # finding.
    # Held by name: `extractor.calls` is the record of every hash the analytical extractor was
    # asked to read, and section 4 asserts against it directly.
    extractor = StubExtractor(RECORDED)
    set_extractor_override(extractor)

    ADMIN = "files-tab-admin"
    PROJ = "PRJ-FILES-01"
    EMPTY = "PRJ-FILES-EMPTY"
    with Session() as s:
        row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
        if row is None:
            s.add(Participant(pseudonymous_code="FILES-ADMIN", role="ResearchAdmin",
                              access_token_hash=hash_access_token(ADMIN)))
        else:
            row.access_token_hash = hash_access_token(ADMIN)
        for legacy in (PROJ, EMPTY):
            if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
                s.add(Project(legacy_id=legacy, doc={"id": legacy, "name": legacy,
                                                     "signals": {}}))
        s.commit()

    admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": "FILES-PM", "role": "Participant",
                    "account_type": "operational"})
    pm = post({"action": "researchlogin",
               "access_token": created["access_token"]})["session_token"]
    for legacy in (PROJ, EMPTY):
        post({"action": "adminmemberadd", "session_token": admin, "id": legacy,
              "participant_id": created["participant_id"], "project_role": "PM"})

    def upload(*names: str, period: int = 1, supersedes: str | None = None) -> dict:
        docs = []
        for n in names:
            entry = {"filename": n, "mimeType": "application/pdf", "dataBase64": b64(blob(n))}
            if supersedes:
                entry["supersedes"] = supersedes
            docs.append(entry)
        return post({"action": "projectupload", "session_token": pm, "id": PROJ,
                     "period": period, "documents": docs})

    def files_view(folder: str | None = None, project: str = PROJ) -> dict:
        payload = {"action": "projectfiles", "session_token": pm, "id": project}
        if folder:
            payload["folder"] = folder
        return post(payload)

    # ================================================================== 1. nothing materialised
    print("\n1. The tree is a template; nothing is materialised per project")
    empty_view = files_view(project=EMPTY)
    check(empty_view.get("ok") is True, "a project that has filed nothing still gets a tree",
          str(empty_view)[:120])
    names = [n["name"] for n in empty_view.get("tree", [])]
    check(names == ["0_PROJ-MGMNT", "1_PROJ INFO", "2_DELIVERABLES", "3_DESIGN", "4_QC",
                    "5_CONST ADMIN", "6_RECEIVED", "NEWFORMA"],
          "the top level is the Arora template, in source order", str(names))
    check(all(not n["occupied"] for n in empty_view["tree"]),
          "and every branch is unoccupied, because no folder was created", "")
    check(empty_view.get("total_files") == 0, "with no files", str(empty_view.get("total_files")))
    with Session() as s:
        tables = [t for t in main_mod.SessionFactory.kw["bind"].dialect.get_table_names(
            s.connection()) if "folder" in t.lower()]
    check(tables == [], "NO folders table exists; the tree is code plus filed paths", str(tables))

    # ================================================================== 2. known type
    print("\n2. A document of a known type files into the expected folder")
    up = upload("payapp.pdf")
    check(up.get("ok") is True, "upload accepted", str(up)[:120])
    entry = up["files"][0]
    check(entry["folder_path"] == "5_CONST ADMIN/5_CONT-PAYMENTS",
          "a pay application files into the contract payments folder",
          str(entry["folder_path"]))
    check(entry["filing_class"] == "analysed", "and is classed as analysed",
          str(entry["filing_class"]))
    check(entry["needs_filing_review"] is False, "and is not flagged for review", "")
    listing = files_view("5_CONST ADMIN/5_CONT-PAYMENTS")
    check([f["filename"] for f in listing["files"]] == ["payapp.pdf"],
          "and the folder lists exactly that file", str(listing["files"])[:120])
    tree_after = files_view()["tree"]
    const = [n for n in tree_after if n["name"] == "5_CONST ADMIN"][0]
    check(const["occupied"] is True, "its branch is now occupied", "")
    check([n for n in tree_after if n["name"] == "0_PROJ-MGMNT"][0]["occupied"] is False,
          "and a branch nothing was filed into is still not", "")

    # ================================================================== 3. low confidence
    print("\n3. A low-confidence placement lands somewhere reviewable and is marked")
    up = upload("maybe.pdf")
    entry = up["files"][0]
    check(entry["folder_path"] == "6_RECEIVED/2026-06-20_INFO",
          "a low-confidence document goes to the received folder, not a discipline folder",
          str(entry["folder_path"]))
    check(entry["needs_filing_review"] is True, "and is flagged for review", "")
    check(entry["classification_confidence"] == 0.20,
          "the confidence the classifier reported is stored",
          str(entry["classification_confidence"]))
    check(files_view()["review_count"] >= 1, "and the project reports something to review",
          str(files_view()["review_count"]))
    # The threshold is a declared constant, not a magic number buried in a branch.
    check(jt.CONFIDENCE_THRESHOLD == 0.70, "the threshold is declared in one place",
          str(jt.CONFIDENCE_THRESHOLD))
    check(jt.needs_review("pay_application", None, jt.CLASS_ANALYSED) is True,
          "no confidence is treated as reviewable, never as confident", "")

    # ================================================================== 4. reference corpus
    print("\n4. A reference document is filed, and never enters the analytical path")
    up = upload("Division 23 Specification.pdf")
    entry = up["files"][0]
    check(entry["filing_class"] == "reference", "a specification is classed as reference",
          str(entry["filing_class"]))
    check(entry["folder_path"].endswith("D_SPECIFICATIONS"),
          "and is filed into the QC specifications folder", str(entry["folder_path"]))
    check(entry["contributes"] is False, "it contributes nothing to the analysis", "")
    check("reference" in (entry.get("note") or ""),
          "and says so as reference material, not as a failure", str(entry.get("note")))
    # The structural guarantee: it is not a mapped type, so the merge cannot read it.
    with Session() as s:
        spec = s.scalar(select(Document).where(
            Document.sha256 == sha(blob("Division 23 Specification.pdf"))))
    si = assemble_signal_inputs([{"sha256": spec.sha256, "doc_type": spec.doc_type,
                                  "filename": spec.filename, "extraction": spec.extraction}])
    blank = assemble_signal_inputs([])
    check(si == blank, "assembling it alone produces exactly the empty signal inputs", "")
    # 2026-08-03. This used to assert doc_type == "unmapped", which was the value the classifier
    # returned after READING the specification. It no longer runs at all for a reference
    # document, so the honest record is that nothing was read: no type, no extraction, no model.
    # That is a stronger statement than "the classifier could not map it" and it is the one the
    # design has always claimed — `reference_kind`'s docstring says routing a specification
    # through the analytical extractor "is precisely what must not happen", and until this date
    # it happened on every upload.
    check(spec.doc_type is None,
          "no type was assigned, because the classifier never saw it", str(spec.doc_type))
    check(spec.extraction is None,
          "and no extraction was recorded for it", str(spec.extraction))
    check(spec.extraction_model is None,
          "and no extraction model was charged for it", str(spec.extraction_model))
    check(entry["status"] == "filed",
          "the upload reports it as filed, not as extracted or as failed",
          str(entry["status"]))

    # THE RULE ITSELF, ASSERTED AGAINST THE EXTRACTOR AND NOT AGAINST A SYMPTOM.
    #
    # `StubExtractor.calls` records the sha256 of every document it was asked to read. The rule
    # in `reference_kind`'s docstring is that a specification must never reach the analytical
    # extractor at all, so the check is simply that its hash is absent from that list.
    #
    # Written this way after a weaker version failed to catch its own fault: asserting only the
    # downstream outcome (status "filed", class reference, no stored extraction) stayed GREEN
    # with the skip removed, because the document was still stored by the reference branch
    # further down and the symptoms therefore looked identical. The extractor call is the thing
    # the design forbids, so the extractor call is what gets asserted.
    check(sha(blob("Division 23 Specification.pdf")) not in extractor.calls,
          "the analytical extractor was NEVER asked to read the specification",
          f"{len(extractor.calls)} call(s) made this run")
    check(sha(blob("payapp.pdf")) in extractor.calls,
          "while an analysable document WAS read, so the check above is not vacuous", "")

    # The gate must stay narrow. A register or an individual form is NOT reference material and
    # must keep going to the analytical classifier, or the storage-redesign register-only rule
    # is silently undone by this fix.
    import app.jdrive_tree as _jt
    for name in ("Submittal 014 shop drawings.pdf", "RFI 233 response.pdf",
                 "submittal register 2026-06.xlsx", "Monthly Report June.pdf"):
        check(_jt.reference_kind(name) is None,
              f"not diverted from the analytical path: {name}",
              str(_jt.reference_kind(name)))

    print("\n   ...and a plainly filed document does not read as a failed extraction")
    up = upload("Tower.rvt")
    entry = up["files"][0]
    check(entry["status"] != "failed", "a Revit model uploads successfully", str(entry)[:100])
    check(entry["filing_class"] == "filed", "and is classed as filed", str(entry["filing_class"]))
    check(entry["folder_path"] == "3_DESIGN/5_BIM-CAD/REVIT_HOST NAME_VERSION (Delete if CAD)",
          "filed by its format into the Revit folder", str(entry["folder_path"]))
    check("not one the analysis reads" in (entry.get("note") or ""),
          "and the note says it is filed, not that anything went wrong",
          str(entry.get("note")))

    # ================================================================== 5. versions
    print("\n5. A second version appears alongside the first, never replacing it")
    upload("rfilog-v1.pdf")
    with Session() as s:
        v1 = s.scalar(select(Document).where(Document.sha256 == sha(blob("rfilog-v1.pdf"))))
        v1_id = v1.document_id
    upload("rfilog-v2.pdf", supersedes=v1_id)
    all_files = files_view()["files"]
    logs = sorted([f for f in all_files if f["filename"].startswith("rfilog")],
                  key=lambda f: f["version"])
    check(len(logs) == 2, "both versions are present in the listing", str(len(logs)))
    check([f["version"] for f in logs] == [1, 2], "numbered 1 and 2", str([f["version"] for f in logs]))
    check(logs[0]["superseded"] is True and logs[1]["superseded"] is False,
          "the first is marked superseded and the second is not", "")
    check(logs[1]["supersedes_document_id"] == v1_id,
          "and the second names the one it replaces", str(logs[1]["supersedes_document_id"]))
    with Session() as s:
        rows = s.scalars(select(DocumentUpload).where(
            DocumentUpload.document_id.in_([v1_id, logs[1]["document_id"]]))).all()
    check(len(rows) == 2 and all(r.folder_path for r in rows),
          "both keep their own upload row and their own folder; nothing is replaced on disk",
          str([(r.document_id[:6], r.folder_path) for r in rows]))

    # ================================================================== 6. preview
    print("\n6. An unsupported format says so rather than being previewed")
    by_name = {f["filename"]: f for f in files_view()["files"]}
    check(by_name["payapp.pdf"]["preview"] == "native", "a PDF previews natively",
          str(by_name["payapp.pdf"]["preview"]))
    check(by_name["Tower.rvt"]["preview"] == "unsupported",
          "a Revit model is reported unsupported", str(by_name["Tower.rvt"]["preview"]))
    upload("notes.xlsx")
    x = [f for f in files_view()["files"] if f["filename"] == "notes.xlsx"][0]
    check(x["preview"] == "download", "a spreadsheet is offered for download",
          str(x["preview"]))
    message = files_view()["unsupported_preview_message"]
    check("not supported" in message.lower() and "download" in message.lower(),
          "and the message names the format problem and the way out", message[:70])
    check("—" not in message, "no em dash in the message (house rule)", "")

    # ================================================================== 7. the two shapes
    print("\n7. The identifier-bearing branches are not flattened into a date rule")
    up = upload("CO-014.pdf")
    claim = up["files"][0]["folder_path"]
    check(claim == "5_CONST ADMIN/8_CLAIMS/CLAIM 014/2026-06-10",
          "a claim is CLAIM number ABOVE the date, two levels", claim)
    up = upload("site obs 3.pdf")
    obs = up["files"][0]["folder_path"]
    check(obs == "5_CONST ADMIN/7_FIELD-SITE VISITS/2026-06-12 SITE OBS 3",
          "a field visit is the identifier INSIDE the dated name, one level", obs)
    check(claim.count("/") == 3 and obs.count("/") == 2,
          "the two shapes have different depths, so neither was flattened",
          f"{claim.count('/')} vs {obs.count('/')}")

    # ================================================================== 8. the gate
    print("\n8. The reference corpus read is gated on the server; filing is not")
    corpus = post({"action": "projectcorpus", "session_token": pm, "id": PROJ})
    check(corpus.get("ok") is True and corpus.get("count") == 1,
          "an operational account with the reviewer on reads the corpus", str(corpus)[:120])
    off = post({"action": "adminfeaturesset", "session_token": admin,
                "participant_id": created["participant_id"], "features": {"auditor": False}})
    check(off.get("ok") is True, "the reviewer can be switched off by an admin", str(off)[:100])
    refused = post({"action": "projectcorpus", "session_token": pm, "id": PROJ})
    check(refused.get("ok") is not True,
          "and the corpus read is then refused by the SERVER, not by hiding a tab",
          str(refused)[:120])
    check("not available" in str(refused.get("error") or ""),
          "with the feature-flag refusal", str(refused.get("error"))[:80])
    # FILING IS NOT CONDITIONAL ON THE FLAG.
    up = upload("Division 23 Specification.pdf", period=2)
    entry = up["files"][0]
    check(entry["filing_class"] == "reference",
          "with the reviewer OFF a specification is still filed as reference",
          str(entry["filing_class"]))
    check(entry["contributes"] is False,
          "and is still kept out of the analytical path", "")
    anon = post({"action": "projectcorpus", "id": PROJ})
    check(anon.get("ok") is not True,
          "an anonymous caller cannot reach the corpus either", str(anon)[:100])
    post({"action": "adminfeaturesset", "session_token": admin,
          "participant_id": created["participant_id"], "features": {"auditor": True}})

    # ================================================================== 9. moving a misfile
    print("\n9. A misfile is visible and correctable")
    target = [f for f in files_view()["files"] if f["filename"] == "maybe.pdf"][0]
    check(target["needs_filing_review"] is True, "precondition: it is flagged for review", "")
    moved = post({"action": "projectfilemove", "session_token": pm, "id": PROJ,
                  "document_id": target["document_id"],
                  "folder": "5_CONST ADMIN/5_CONT-PAYMENTS"})
    check(moved.get("ok") is True, "the PM can move it", str(moved)[:120])
    after = [f for f in files_view()["files"] if f["filename"] == "maybe.pdf"][0]
    check(after["folder_path"] == "5_CONST ADMIN/5_CONT-PAYMENTS", "it is in the new folder",
          str(after["folder_path"]))
    check(after["needs_filing_review"] is False,
          "and the review is resolved, because a human has now decided", "")
    bad = post({"action": "projectfilemove", "session_token": pm, "id": PROJ,
                "document_id": target["document_id"], "folder": "../etc"})
    check(bad.get("ok") is not True and "Arora" in str(bad.get("error")),
          "a destination outside the Arora structure is refused by name",
          str(bad.get("error"))[:80])
    pattern = post({"action": "projectfilemove", "session_token": pm, "id": PROJ,
                    "document_id": target["document_id"],
                    "folder": "6_RECEIVED/YYYY-MM-DD_INFO"})
    check(pattern.get("ok") is not True,
          "and so is a naming PATTERN, which is not a folder", str(pattern.get("error"))[:80])


try:
    main()
except Exception as e:  # a crash must read as a FAILURE, never as a clean run
    import traceback
    traceback.print_exc()
    check(False, f"suite crashed: {type(e).__name__}: {e}")
finish()
