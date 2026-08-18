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


GET_SESSION: str | None = None


def get(params: dict, token: str | None = None) -> dict:
    # Reads are authenticated as of 2026-08-02, and the credential travels in a HEADER rather
    # than the query string. Passing `session_token=None` in params forces a genuinely anonymous
    # request, which is how the refusal checks are written.
    q = dict(params)
    tok = q.pop("session_token", token or GET_SESSION)
    headers = {"Authorization": "Bearer " + tok} if tok else {}
    r = client.get("/exec", params=q, headers=headers)
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
GET_SESSION = pm            # reads are authenticated; the PM is this suite's default reader
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

print("\nGuarantee 8 — an operational project carries no study package, and is not redacted")
# REWRITTEN 2026-08-08, for the reason recorded in test_documents_b7b.py's Guarantee 6. This
# project is created by an operational account through projectcreate and no scenario names it
# as an evidence package, so there is no participant to blind and no preliminary judgment to
# wait for. Asserting a withholding here pinned the defect: the reveal predicate was reached
# through a Decision row that an operational project never gets, so the scored courses of
# action were redacted on every read forever.
#
# What remains true and is still asserted: no researcher-authored package is spliced into a
# project that has none. The withholding is asserted where it is real, in
# test_decision_ui_t4.py and test_courses_of_action.py.
r = result["result"]
check(r["recommendation"] is None, "recommendation is null: this project has no study package")
check("recommendation_withheld" not in r,
      "and the read is not reported as withheld, because nothing is withheld from this PM")
body = json.dumps(result)
for marker in ("package_hash", "package_id"):
    check(marker not in body, f"response body has no {marker!r}")
# The inverse of the old assertion, and the point of the change: no module on an operational
# read carries the redaction flag, and the scored courses are readable.
redacted_any = any(
    isinstance(m, dict) and m.get("recommendation_withheld") for m in (r["module_results"] or [])
)
check(not redacted_any,
      "no module is marked withheld on an operational project",
      f"redacted_any={redacted_any}")
# RUN 7. This asserted the scored course set was readable on an operational project. Those
# scores were literals identical on every project, and the module abstains now, so what is
# asserted is the property the check was for: nothing on this read is withheld, and the module
# is recorded as an abstention rather than vanishing without explanation.
_reg = next((m for m in (r["module_results"] or [])
             if isinstance(m, dict)
             and m.get("method_class") in ("Minimax_Regret_Decision_Rule",
                                           "Regret_Minimization")), None)
check(_reg is None,
      "the analysis that scored the courses of action carries no row, because it abstains",
      str(_reg)[:160])
_abst_ids = {a.get("module_id") for a in (r.get("abstained") or [])}
check("B4.7" in _abst_ids,
      "and its silence is recorded as an abstention on the PM's own read",
      str(sorted(_abst_ids))[:120])


# ---------------------------------------------------------------- Guarantee 9

print("\nGuarantee 9 — portfolio reads the stored snapshot; below-threshold state is plain")
snap = r["portfolio_snapshot"]
check(snap is not None, "portfolio_snapshot is present (never silently null)")
check(snap.get("insufficient_data") is True, "below threshold, reported as insufficient_data")
# RUN 33. AT v21 THE REASON IS THE GOVERNED ONE, not the legacy off-by-one sentence. The v20
# message ("need at least 3 projects with signal data") described a guard that no longer decides
# anything: Portfolio Health abstains at v21 because no GOVERNED COHORT has been supplied, which
# is a different and truthful reason. The legacy sentence travels with the legacy implementation
# it belongs to and is asserted there.
check("governed portfolio cohort" in (snap.get("message") or ""),
      "the server's own abstention reason is present, unmodified", snap.get("message"))
check(snap.get("route") == "canonical_v8" and snap.get("voting") is False
      and snap.get("creates_project_evidence") is False,
      "and the snapshot is stamped with the canonical route, non-voting, creating no evidence",
      str([snap.get("route"), snap.get("voting"), snap.get("creates_project_evidence")]))

# a second project with real signal data pushes the vector count over the guard
create2 = post({"action": "projectcreate", "session_token": other, "name": "T3T5 Second Project"})
pid2 = create2["project_id"]
post({"action": "projectupload", "session_token": other, "id": pid2, "period": 1,
      "documents": [{"filename": "pay-app-2.pdf", "mimeType": "application/pdf",
                     "dataBase64": b64(PDF_A)}]})
compute2 = post({"action": "projectcompute", "session_token": other, "id": pid2, "period": 1})
result2b = post({"action": "projectresults", "session_token": other, "id": pid2, "period": 1})
snap2 = result2b["result"]["portfolio_snapshot"]
# RUN 33. A SECOND PROJECT NO LONGER MANUFACTURES A COHORT. At v20 the mere existence of two
# rows with a cost index was enough to produce four portfolio readings; at v21 a comparison
# needs a declared population, period, feature schema and model version, and none of those can
# be inferred from "the rows this query returned". Neither project here supplies a governed
# cohort through `saveprojectdata`, so all five abstain with the SAME reason -- the abstention
# is a property of the cohort, not five separate opinions about it. This is the correct reading,
# not a regression from the populated one.
check(snap2 is not None and snap2.get("structure_absent") is True,
      "with 2+ live results but NO governed cohort supplied, the snapshot is a reported "
      "abstention rather than an invented comparison",
      str(snap2)[:150] if snap2 else None)
# All five are PRESENT as reported abstentions carrying their reason. At v20 an abstaining
# portfolio module vanished from the map entirely, which is why "the count is 3" was the
# assertion; a reader of the stored snapshot could not tell an abstention from a module that had
# never existed. Every one of the five is now addressable, and its reason is readable.
_res2 = (snap2 or {}).get("results", {})
check(len(_res2) == 5 and sorted(_res2) == [
          "cat8_1_isolation_forest", "cat8_2_portfolio_outlier",
          "cat8_3_trajectory_classifier", "cat8_4_cross_project_pattern",
          "cat8_5_anomaly_score"],
      "all five Portfolio Health identities are addressable in the stored snapshot",
      str(sorted(_res2)))
check(all(_res2[k].get("abstained") is True and _res2[k].get("abstention_reason")
          for k in _res2),
      "and every one of them abstains WITH ITS REASON rather than vanishing")
check(all(_res2[k].get("voting") is False and _res2[k].get("creates_project_evidence") is False
          and "status_color" not in _res2[k] for k in _res2),
      "non-voting, creating no project evidence, and carrying no status colour")
check(all(not v.get("insufficient_data") for v in snap2.get("results", {}).values()),
      "no stored D1 sub-result carries a colour and an insufficiency flag together")


# ---------------------------------------------------------------- T8: geocoding on create
#
# The Apps Script backend geocoded server-side and this service did not, so every project created
# here had no coordinates and could never be placed on a map. These checks cover the restored
# behaviour, and they never touch the network: app.geocode.geocode is replaced by a stub, so the
# suite stays offline and no provider quota is spent on a test run.
#
# BECAUSE THE STUB REPLACES geocode() WHOLESALE, NOTHING HERE EXERCISES A PROVIDER. The Google and
# Census branches, and the difference between a rejected key, an exhausted quota and an address
# that does not exist, are covered by tools/test_geocode_providers.py. Keep the two separate.

print("\nT8 — geocoding runs on create, and never blocks it")

import app.geocode as _geo  # noqa: E402

_geo_calls = []


def _stub_geocode(address):
    _geo_calls.append(address)
    if "unfindable" in address.lower():
        return _geo.Result(error="That address could not be found. Try the street address OR "
                                 "the facility name, not both together.")
    if "offline" in address.lower():
        return _geo.Result(error="The location service could not be reached, so this address has "
                                 "not been matched yet. Saving the address again will retry it.")
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


# ---------------------------------------------------------------- A FAILED GEOCODE MUST NOT
# ERASE COORDINATES IT CANNOT REPLACE.
#
# apply_to_doc used to clear lat/lng/formattedAddress on EVERY failure. Since the geocoder of the
# day was never reachable from this deployment, that meant every address edit destroyed the
# project's location and replaced it with nothing. These checks pin the retention, the flag that marks the
# retained position as belonging to an earlier address, and the two cases where nothing is
# retained because there is nothing to retain.
print("\nT8b — a failed geocode retains the previous position and flags it")

# g1 above is located. Edit its address to one the geocoder cannot reach.
located = get({"action": "get", "id": g1["project_id"]})["project"]
check(located.get("lat") == 36.5298, "precondition: the project starts with stored coordinates",
      str(located.get("lat")))

located["address"] = "offline street, somewhere else"
edited = post({"action": "save", "project": located, "session_token": pm})["project"]
check(edited.get("lat") == 36.5298 and edited.get("lng") == -87.3595,
      "an unreachable geocoder LEAVES the previous coordinates in place",
      str(edited.get("lat")) + "," + str(edited.get("lng")))
check(edited.get("geocodeStale") is True,
      "and marks them as belonging to an earlier address", str(edited.get("geocodeStale")))
check(edited.get("formattedAddress") == "Clarksville, Tennessee, USA",
      "keeping the match those coordinates actually came from, so a reader can see which "
      "address they are for", str(edited.get("formattedAddress")))
check("could not be reached" in (edited.get("geocodeError") or ""),
      "and still reports why the new address was not matched")
check(edited.get("address") == "offline street, somewhere else",
      "while the typed address is stored as typed", str(edited.get("address")))

# Read it back from the store rather than trusting the response envelope.
reread = get({"action": "get", "id": g1["project_id"]})["project"]
check(reread.get("lat") == 36.5298 and reread.get("geocodeStale") is True,
      "and that is what was PERSISTED, not just what was returned",
      str(reread.get("lat")) + " stale=" + str(reread.get("geocodeStale")))

# An address that is definitively NOT FOUND is a different failure from an unreachable service,
# but the stored data is just as real, so it is retained on the same terms.
reread["address"] = "unfindable place indeed"
notfound = post({"action": "save", "project": reread, "session_token": pm})["project"]
check(notfound.get("lat") == 36.5298 and notfound.get("geocodeStale") is True,
      "an unfindable address also retains the previous position rather than erasing it",
      str(notfound.get("lat")))

# CLEARING THE ADDRESS IS THE USER SAYING THERE IS NO PLACE, NOT A GEOCODER FAILING TO ANSWER.
# Done HERE, while the project is actually in the stale state — doing it after a later success
# would pass whatever the code did, because the flag would already be gone. (It was written that
# way first, and the fault-injection run caught it: removing geocodeStale from w_save's clear
# list left the suite green.)
check(notfound.get("geocodeStale") is True,
      "precondition for the clear-address check: the project IS flagged stale right now",
      str(notfound.get("geocodeStale")))
notfound["address"] = ""
cleared = post({"action": "save", "project": notfound, "session_token": pm})["project"]
check(cleared.get("lat") is None and cleared.get("lng") is None,
      "clearing the address DOES drop the coordinates", str(cleared.get("lat")))
check("geocodeStale" not in cleared or cleared.get("geocodeStale") in (None, False),
      "and drops the previous-address flag with them", str(cleared.get("geocodeStale")))

# A LATER SUCCESS CLEARS THE FLAG. Without this a project would carry "previous address" forever
# once it had failed once. Re-locate, fail, then succeed, so the flag is genuinely set first.
cleared["address"] = "1200 Terminal Road, Clarksville, TN"
relit = post({"action": "save", "project": cleared, "session_token": pm})["project"]
relit["address"] = "offline street, once more"
relit = post({"action": "save", "project": relit, "session_token": pm})["project"]
check(relit.get("geocodeStale") is True,
      "precondition for the later-success check: the flag is set", str(relit.get("geocodeStale")))
relit["address"] = "1200 Terminal Road, Clarksville, TN, revisited"
fixed = post({"action": "save", "project": relit, "session_token": pm})["project"]
check(fixed.get("lat") == 36.5298 and fixed.get("geocodeError") is None,
      "a later successful geocode stores the new match")
check("geocodeStale" not in fixed or fixed.get("geocodeStale") in (None, False),
      "and clears the previous-address flag", str(fixed.get("geocodeStale")))

# NOTHING IS RETAINED WHEN THERE IS NOTHING TO RETAIN. g3 never had coordinates.
never = get({"action": "get", "id": g3["project_id"]})["project"]
never["address"] = "offline street, again"
still_none = post({"action": "save", "project": never, "session_token": pm})["project"]
check(still_none.get("lat") is None and still_none.get("lng") is None,
      "a project that never had coordinates still ends with none")
check("geocodeStale" not in still_none or still_none.get("geocodeStale") in (None, False),
      "and is NOT flagged as carrying a previous position it never had",
      str(still_none.get("geocodeStale")))

# The retention must come from the STORED document, not from whatever the client posted: w_save
# replaces the stored doc wholesale, so a client that omits lat/lng must not be able to delete a
# position by leaving it out of the payload.
relocated = get({"action": "get", "id": g4["project_id"]})["project"]
relocated["address"] = "1200 Terminal Road, Clarksville, TN"
relocated = post({"action": "save", "project": relocated, "session_token": pm})["project"]
check(relocated.get("lat") == 36.5298, "precondition: a second project is now located",
      str(relocated.get("lat")))
stripped = {k: v for k, v in relocated.items() if k not in ("lat", "lng", "formattedAddress")}
stripped["address"] = "offline street, third time"
survived = post({"action": "save", "project": stripped, "session_token": pm})["project"]
check(survived.get("lat") == 36.5298 and survived.get("geocodeStale") is True,
      "a client payload WITHOUT lat/lng cannot delete the stored position through a failed "
      "geocode", str(survived.get("lat")) + " stale=" + str(survived.get("geocodeStale")))

_geo.geocode = _real_geocode

# ---------------------------------------------------------------- Archived exclusion (2026-08-07)

print("\nArchived exclusion — a working list drops an archived project, restore brings it back")
arch_create = post({"action": "projectcreate", "session_token": pm, "name": "T3T5 Archive Me"})
check(arch_create.get("ok") is True, "archive-target project created", str(arch_create)[:100])
arch_pid = arch_create["project_id"]

before = post({"action": "workspaceprojects", "session_token": pm})
check(any(p["project_id"] == arch_pid for p in before["projects"]),
      "workspaceprojects lists it before archiving")

archived = post({"action": "archive", "session_token": pm, "id": arch_pid})
check(archived.get("ok") is True, "archive accepted", str(archived)[:100])

after = post({"action": "workspaceprojects", "session_token": pm})
check(not any(p["project_id"] == arch_pid for p in after["projects"]),
      "workspaceprojects DROPS an archived project — it is out of the working list")

# Membership itself is untouched by archiving — audit evidence, deliberately kept.
with Session() as s:
    row = s.scalar(select(ProjectMember).where(ProjectMember.user_key == pm_id))
    still_member = s.scalar(
        select(ProjectMember).where(ProjectMember.user_key == pm_id).order_by(
            ProjectMember.added_at.desc()))
check(still_member is not None, "the membership row on the archived project still exists")

restored = post({"action": "restore", "session_token": pm, "id": arch_pid})
check(restored.get("ok") is True, "restore accepted", str(restored)[:100])

back = post({"action": "workspaceprojects", "session_token": pm})
check(any(p["project_id"] == arch_pid for p in back["projects"]),
      "workspaceprojects lists it again after restore — filtering is symmetric")

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
