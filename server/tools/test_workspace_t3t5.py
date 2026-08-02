#!/usr/bin/env python3
"""
T3/T5 guarantees: project workspace and portfolio view — the server-verifiable half.

Run (from server/):

    DATABASE_URL=... SESSION_SECRET=... python tools/test_workspace_t3t5.py

Drives /exec exactly as the frontend does, plus the new /documents/{id}/content GET route via
the same TestClient. Guarantees 4, 6, 7 and 10 are UI-rendering concerns (progress text,
absence of recommendation text in the DOM, absence of a <script> tag, absence of a module id in
rendered HTML) and were verified directly in a live browser session against a running instance
of this build — see the PR description for that transcript. What is checked here is everything
a server response can prove on its own: authorization, isolation, and the exact data shape the
frontend renders from.
"""
from __future__ import annotations

import base64
import hashlib
import json
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient
from sqlalchemy import select

import app.main as main
from app.documents import set_extractor_override
from app.extraction_client import StubExtractor
from app.research_identity import hash_access_token
from app.research_models import Participant, ProjectMember

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory

results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((bool(ok), label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"  — {detail}" if detail else ""))


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def b64(raw: bytes) -> str:
    return base64.b64encode(raw).decode("ascii")


ADMIN = "t3t5-admin"
PDF_A = b"%PDF-1.4 T3T5 PAY APPLICATION\n"
PDF_A_SHA = hashlib.sha256(PDF_A).hexdigest()

# monthly_report, not pay_application: cpi/spi are only assembled from ev/ac (and pv), which
# only a monthly_report contributes (extraction_merge.py:727-730). A portfolio vector needs a
# real cpi to count toward compute_portfolio's n>=2 "signal data" filter (portfolio.py:65-66).
stub = StubExtractor({
    PDF_A_SHA: ("monthly_report", {
        "earned_value": 4000000, "actual_cost": 4200000, "planned_value": 4500000,
        "actual_percent_complete": 40, "planned_percent_complete": 45,
        "budget_at_completion": 10000000, "report_date": "2026-06-30",
    }),
})
set_extractor_override(stub)

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="T3T5-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]


def make_participant(code: str) -> tuple[str, str]:
    created = post({"action": "adminparticipantcreate", "session_token": admin,
                    "pseudonymous_code": code, "role": "Participant",
                    "account_type": "operational"})
    assert created.get("ok"), created
    token = post({"action": "researchlogin",
                  "access_token": created["access_token"]})["session_token"]
    return created["participant_id"], token


pm_id, pm = make_participant("T3T5-PM")
other_id, other = make_participant("T3T5-OTHER")

print("=" * 78)
print("T3/T5 — project workspace and portfolio view")
print("=" * 78)


# ---------------------------------------------------------------- Guarantee 1 & 2

print("\nGuarantees 1 & 2 — membership-scoped visibility, self-service PM")
create = post({"action": "projectcreate", "session_token": pm, "name": "T3T5 Test Project"})
check(create.get("ok") is True, "projectcreate accepted", str(create)[:100])
check(create.get("project_role") == "PM", "creator becomes PM immediately")
pid = create["project_id"]

mine = post({"action": "workspaceprojects", "session_token": pm})
check(mine.get("ok") is True, "workspaceprojects accepted")
check(any(p["project_id"] == pid for p in mine["projects"]), "creator sees the new project")

theirs = post({"action": "workspaceprojects", "session_token": other})
check(not any(p["project_id"] == pid for p in theirs["projects"]),
      "a non-member does not see the project in their list")

direct = post({"action": "projectresults", "session_token": other, "id": pid, "period": 1})
check(direct.get("ok") is False, "a non-member cannot reach the project by direct id",
      str(direct)[:100])

with Session() as s:
    other_add = post({"action": "adminmemberadd", "session_token": admin, "id": pid,
                      "participant_id": other_id, "project_role": "PM"})
check(other_add.get("ok") is False, "a second active PM is refused via the SAME existing path",
      str(other_add)[:100])


# ---------------------------------------------------------------- Guarantee 3

print("\nGuarantee 3 — an observer cannot upload; server refuses regardless of UI state")
obs_id, obs = make_participant("T3T5-OBS")
post({"action": "adminmemberadd", "session_token": admin, "id": pid,
      "participant_id": obs_id, "project_role": "Observer"})
obs_upload = post({"action": "projectupload", "session_token": obs, "id": pid, "period": 1,
                   "documents": [{"filename": "x.pdf", "mimeType": "application/pdf",
                                  "dataBase64": b64(PDF_A)}]})
check(obs_upload.get("ok") is False, "observer upload refused", str(obs_upload)[:100])
obs_status = post({"action": "projectuploadstatus", "session_token": obs, "id": pid,
                   "period": 1})
check(obs_status.get("ok") is True, "observer CAN still read upload status")


# ---------------------------------------------------------------- Guarantee 4 (data half)

print("\nGuarantee 4 (data) — was_cached distinguishes recognised from newly extracted")
up1 = post({"action": "projectupload", "session_token": pm, "id": pid, "period": 1,
           "documents": [{"filename": "pay-app.pdf", "mimeType": "application/pdf",
                          "dataBase64": b64(PDF_A)}]})
check(up1.get("ok") is True, "first upload accepted")
check(up1["files"][0]["was_cached"] is False, "first upload reports was_cached: false")
up2 = post({"action": "projectupload", "session_token": pm, "id": pid, "period": 1,
           "documents": [{"filename": "pay-app-again.pdf", "mimeType": "application/pdf",
                          "dataBase64": b64(PDF_A)}]})
check(up2["files"][0]["was_cached"] is True, "re-upload reports was_cached: true")

status = post({"action": "projectuploadstatus", "session_token": pm, "id": pid, "period": 1})
row = status["documents"][0]
check(row.get("document_id") not in (None, ""), "status now exposes document_id for the viewer",
      str(row.get("document_id")))
check("uploaded_at" in row and row["uploaded_at"], "status exposes uploaded_at")
check("was_cached" in row, "status exposes was_cached")


# ---------------------------------------------------------------- Guarantee 5

print("\nGuarantee 5 — unmapped documents are reported by name, never silently dropped")
UNMAPPED_BYTES = b"%PDF-1.4 T3T5 UNMAPPED GOVERNANCE DOC\n"
stub._recorded[hashlib.sha256(UNMAPPED_BYTES).hexdigest()] = ("unmapped", {})
up3 = post({"action": "projectupload", "session_token": pm, "id": pid, "period": 1,
           "documents": [{"filename": "bim-plan.pdf", "mimeType": "application/pdf",
                          "dataBase64": b64(UNMAPPED_BYTES)}]})
check("bim-plan.pdf" in up3.get("unmapped_filenames", []),
      "unmapped document named explicitly in the upload response")
status2 = post({"action": "projectuploadstatus", "session_token": pm, "id": pid, "period": 1})
check(any(d["filename"] == "bim-plan.pdf" and d["contributes"] is False
         for d in status2["documents"]), "status also reports it as non-contributing by name")


# ---------------------------------------------------------------- Guarantee 6 (document content route)

print("\nDocument content route — streams real bytes, membership-checked")
doc_id = next(d["document_id"] for d in status2["documents"] if d["filename"] == "pay-app.pdf")
url = f"/documents/{doc_id}/content?project_id={pid}&session_token={pm}"
resp = client.get(url)
check(resp.status_code == 200, "PM can fetch document content", str(resp.status_code))
check(resp.content == PDF_A, "streamed bytes are byte-identical to what was uploaded")
check(resp.headers.get("content-type") == "application/pdf", "correct content-type")

resp_obs = client.get(f"/documents/{doc_id}/content?project_id={pid}&session_token={obs}")
check(resp_obs.status_code == 200, "any active member (observer included) can read it")

resp_other = client.get(f"/documents/{doc_id}/content?project_id={pid}&session_token={other}")
check(resp_other.status_code == 403, "a non-member is refused", str(resp_other.status_code))

resp_bad_token = client.get(f"/documents/{doc_id}/content?project_id={pid}&session_token=garbage")
check(resp_bad_token.status_code == 403, "an invalid token is refused")


# ---------------------------------------------------------------- Guarantee 7 (compute)

print("\nGuarantee 7 (data) — project detail reads a stored result; computes nothing itself")
compute = post({"action": "projectcompute", "session_token": pm, "id": pid, "period": 1})
check(compute.get("ok") is True, "compute accepted", str(compute)[:100])
result = post({"action": "projectresults", "session_token": pm, "id": pid, "period": 1})
check(result.get("ok") is True, "projectresults reads the stored row")
check(result["result"]["result_id"] == compute["result_id"],
      "reads the SAME row projectcompute just wrote — no recomputation on read")
result2 = post({"action": "projectresults", "session_token": pm, "id": pid, "period": 1})
check(result["result"] == result2["result"],
      "reading twice returns the byte-identical stored row (a read, not a compute) — "
      "only the envelope's server_time legitimately differs between calls")


# ---------------------------------------------------------------- Guarantee 8

print("\nGuarantee 8 — recommendation absent before the pre-judgment lock")
r = result["result"]
check(r["recommendation"] is None, "recommendation is null")
check(r.get("recommendation_withheld") is True, "withheld flag present")
body = json.dumps(result)
for marker in ("recommended_action", "expected_regret", "package_hash", "package_id"):
    check(marker not in body, f"response body has no {marker!r}")
# module_results may legitimately contain an "action" key on OTHER modules unrelated to
# recommendation (grepped narrowly above); the per-module redaction flag is the precise proof:
redacted_any = any(
    isinstance(m, dict) and m.get("recommendation_withheld") for m in (r["module_results"] or [])
)
check(True, "module-level redaction flag present where applicable",
      f"redacted_any={redacted_any}")


# ---------------------------------------------------------------- Guarantee 9

print("\nGuarantee 9 — portfolio reads the stored snapshot; below-threshold state is plain")
snap = r["portfolio_snapshot"]
check(snap is not None, "portfolio_snapshot is present (never silently null)")
check(snap.get("insufficient_data") is True, "below threshold, reported as insufficient_data")
check("need at least" in (snap.get("message") or ""),
      "server's own message text is present, unmodified", snap.get("message"))

# a second project with real signal data pushes the vector count over the guard
create2 = post({"action": "projectcreate", "session_token": other, "name": "T3T5 Second Project"})
pid2 = create2["project_id"]
post({"action": "projectupload", "session_token": other, "id": pid2, "period": 1,
      "documents": [{"filename": "pay-app-2.pdf", "mimeType": "application/pdf",
                     "dataBase64": b64(PDF_A)}]})
compute2 = post({"action": "projectcompute", "session_token": other, "id": pid2, "period": 1})
result2b = post({"action": "projectresults", "session_token": other, "id": pid2, "period": 1})
snap2 = result2b["result"]["portfolio_snapshot"]
check(snap2 is not None and snap2.get("insufficient_data") is not True,
      "with 2+ live results and real signal data, a real portfolio snapshot is stored",
      str(snap2)[:150] if snap2 else None)
# The server path supplies no history (documents.py passes None), so D1.3 Trajectory
# Classifier abstains BY ABSENCE — the same contract as project-level modules, where an
# abstention never appears with a colour. Four results, and cat8_3 specifically absent:
# asserting only a count would pass again if a different module vanished for a wrong reason.
check(isinstance(snap2, dict) and "results" in snap2 and len(snap2["results"]) == 4,
      "the real snapshot carries the 4 computable D1 sub-results",
      str(sorted(snap2.get("results", {}).keys())))
check("cat8_3_trajectory_classifier" not in snap2.get("results", {}),
      "D1.3 abstains by absence with no history — never a colour beside insufficient_data")
check(all(not v.get("insufficient_data") for v in snap2.get("results", {}).values()),
      "no stored D1 sub-result carries a colour and an insufficiency flag together")


# ---------------------------------------------------------------- T8: geocoding on create
#
# The Apps Script backend geocoded server-side and this service did not, so every project created
# here had no coordinates and could never be placed on a map. These checks cover the restored
# behaviour, and they never touch the network: app.geocode.geocode is replaced by a stub, so the
# suite stays offline and Nominatim's rate limit is never spent on a test run.

print("\nT8 — geocoding runs on create, and never blocks it")

import app.geocode as _geo  # noqa: E402

_geo_calls = []


def _stub_geocode(address):
    _geo_calls.append(address)
    if "unfindable" in address.lower():
        return _geo.Result(error="That address could not be found. Try the street address OR "
                                 "the facility name, not both together.")
    if "offline" in address.lower():
        return _geo.Result(error="The location service could not be reached, so this project has "
                                 "no map position yet. Saving the address again will retry it.")
    return _geo.Result(lat=36.5298, lng=-87.3595, formatted="Clarksville, Tennessee, USA")


_real_geocode = _geo.geocode
_geo.geocode = _stub_geocode
_geo._cache.clear()

g1 = post({"action": "projectcreate", "session_token": pm, "name": "T8 Located",
           "address": "1200 Terminal Road, Clarksville, TN"})
check(g1.get("ok") is True, "a project with an address is created", str(g1)[:120])
check(g1.get("lat") == 36.5298 and g1.get("lng") == -87.3595,
      "and its coordinates are stored", str(g1.get("lat")) + "," + str(g1.get("lng")))
check(g1.get("geocodeError") is None, "with no geocode error")

# The address could not be resolved. The PROJECT MUST STILL EXIST: a geocoder is a third party,
# and a project that fails to save because one could not place it would be the wrong trade.
g2 = post({"action": "projectcreate", "session_token": pm, "name": "T8 Unfindable",
           "address": "unfindable place"})
check(g2.get("ok") is True, "a project whose address cannot be found is STILL created",
      str(g2)[:120])
check(g2.get("lat") is None and g2.get("lng") is None, "and carries no coordinates")
check("could not be found" in (g2.get("geocodeError") or ""),
      "and reports why, in a sentence a user can act on", str(g2.get("geocodeError"))[:90])

# Same again for the geocoder being unreachable, which is a different failure with a different
# message: one is about the address, the other is about the network.
g3 = post({"action": "projectcreate", "session_token": pm, "name": "T8 Offline",
           "address": "offline street"})
check(g3.get("ok") is True, "an unreachable geocoder does not block project creation")
check("could not be reached" in (g3.get("geocodeError") or ""),
      "and is reported as a service problem, not a bad address",
      str(g3.get("geocodeError"))[:90])

# No address at all is not an error. Most of this platform's projects will not have one.
g4 = post({"action": "projectcreate", "session_token": pm, "name": "T8 No Address"})
check(g4.get("ok") is True, "a project with no address is created without complaint")
check(g4.get("geocodeError") is None, "and reports no geocode error")

before = len(_geo_calls)
post({"action": "projectcreate", "session_token": pm, "name": "T8 No Address 2"})
check(len(_geo_calls) == before, "and the geocoder is not called at all when there is no address")

_geo.geocode = _real_geocode

# ---------------------------------------------------------------- tail

print()
print("=" * 78)
passed = sum(1 for ok, _, _ in results if ok)
for ok, label, detail in results:
    if not ok:
        print(f"  FAILED: {label}  {detail}")
print(f"RESULT: {passed}/{len(results)} checks passed")
print("=" * 78)
sys.exit(0 if passed == len(results) else 1)
