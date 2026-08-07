#!/usr/bin/env python3
"""
A1b regression: the /exec write surface, round-tripped.

The original A1b verification (commit 2fc62dd, "47 of 47 round-trip checks pass") was run from
an uncommitted scratch harness. This file is the committed replacement, added in B8 so the write
surface has a rerunnable regression: every write action is round-tripped through /exec and
verified by reading back, plus the conflict shapes, the deferred-action wording, and the B8
property that sessionless facade writes are unchanged even on a project that has members.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_writes_a1b.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import select  # noqa: E402

import app.main as main  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import Participant  # noqa: E402

client = TestClient(main.app, raise_server_exceptions=False)
Session = main.SessionFactory
results: list[tuple[bool, str, str]] = []


def check(ok: bool, label: str, detail: str = "") -> None:
    results.append((ok, label, detail))
    print(f"  {'PASS' if ok else 'FAIL'}  {label}" + (f"   {detail}" if detail and not ok else ""))


# The facade FAILS CLOSED on writes as of 2026-08-02, so this harness has to sign in. It used to
# post every write with no session at all, which is exactly what an anonymous attacker was doing.
# `post` attaches the operational session below unless a payload sets its own (or sets it to None,
# which is how the unauthenticated checks near the end are written).
SESSION: str | None = None


def post(payload: dict) -> dict:
    body = dict(payload)
    if "session_token" in body and body["session_token"] is None:
        body.pop("session_token")
    elif "session_token" not in body and SESSION:
        body["session_token"] = SESSION
    r = client.post("/exec", content=json.dumps(body), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def get(params: dict) -> dict:
    # Reads are authenticated as of 2026-08-02, and the credential travels in a HEADER rather
    # than the query string. Passing `session_token=None` in params forces a genuinely anonymous
    # request, which is how the refusal checks are written.
    q = dict(params)
    tok = q.pop("session_token", SESSION)
    headers = {"Authorization": "Bearer " + tok} if tok else {}
    r = client.get("/exec", params=q, headers=headers)
    assert r.status_code == 200
    return r.json()


P1, P2, P3 = "PRJ-A1B-01", "PRJ-A1B-02", "PRJ-A1B-03"

# Sign in before the first write. Operational, so the account-type gate on `create` lets it
# through; not a member of any project here, so the B8 PM rule is exercised separately below.
_WRITER = "a1b-writer-token"
with Session() as _s:
    _s.add(Participant(pseudonymous_code="A1B-WRITER", role="Participant",
                       account_type="operational",
                       access_token_hash=hash_access_token(_WRITER)))
    _s.commit()
_login = client.post("/exec", content=json.dumps(
    {"action": "researchlogin", "username": "A1B-WRITER", "password": _WRITER}),
    headers={"Content-Type": "text/plain"}).json()
SESSION = _login["session_token"]
WRITER_ID = _login["participant_id"]

print("=" * 78)
print("CREATE")
print("=" * 78)
r = post({"action": "create", "id": P1, "name": "A1b One", "sector": "Aviation"})
check(r.get("ok") is True and r["project"]["id"] == P1, "create round-trips", str(r)[:160])
check(r["project"]["events"][0]["event"] == "project_created", "project_created event present")
check(bool(r["project"]["createdAt"]) and r["project"]["createdAt"] == r["project"]["updatedAt"],
      "server-assigned createdAt == updatedAt on create")
check(post({"action": "create"}).get("error") == "Missing id", "create without id refused")
check("invalid characters" in post({"action": "create", "id": "bad id!"}).get("error", ""),
      "invalid characters refused")
check(post({"action": "create", "id": P1}).get("error") == f"Project number already exists: {P1}",
      "duplicate id refused with live wording")

print()
print("=" * 78)
print("SAVE and optimistic concurrency")
print("=" * 78)
doc = post({"action": "create", "id": P2})["project"]
doc["name"] = "A1b Two edited"
r = post({"action": "save", "project": doc})
check(r.get("ok") is True and r["project"]["name"] == "A1b Two edited", "save round-trips",
      str(r)[:160])
check(r["project"]["updatedAt"] != doc["updatedAt"], "updatedAt is server-reassigned on save")
check(r["project"]["createdAt"] == doc["createdAt"], "createdAt preserved from the stored doc")
stale = dict(doc)  # still carries the pre-save updatedAt
stale["name"] = "stale write"
r = post({"action": "save", "project": stale})
check(r.get("ok") is False and "Stale write" in r.get("error", ""),
      "stale updatedAt refused as ok:false", str(r)[:160])
check(post({"action": "save"}).get("error") == "Missing project",
      "save without a project payload refused")
fresh = get({"action": "get", "id": P2})["project"]
r = post({"action": "save", "project": fresh, "record_version": 999})
check(r.get("ok") is False and "record_version 999" in r.get("error", ""),
      "stale record_version refused", str(r)[:160])
r = post({"action": "save", "project": {"id": "PRJ-NOPE"}})
check(r.get("error") == "Not found: PRJ-NOPE", "save of unknown project refused")

print()
print("=" * 78)
print("ARCHIVE / RESTORE")
print("=" * 78)
r = post({"action": "archive", "id": P2})
check(r.get("ok") is True and r.get("archived") is True, "archive ok", str(r)[:120])
check(get({"action": "get", "id": P2}).get("error") == f"Not found: {P2}",
      "archived project is Not found on get (live wording)")
check(any(p["id"] == P2 for p in get({"action": "listarchived"})["projects"]),
      "archived project appears in listarchived")
check(f"exists in archive" in post({"action": "create", "id": P2}).get("error", ""),
      "recreating an archived id refused with archive wording")
r = post({"action": "restore", "id": P2})
check(r.get("ok") is True and r.get("restored") is True, "restore ok", str(r)[:120])
check(get({"action": "get", "id": P2}).get("ok") is True, "restored project readable again")
check("Archived project not found" in post({"action": "restore", "id": P2}).get("error", ""),
      "restoring a non-archived project refused")

print()
print("=" * 78)
print("SETPROJECTNUMBER")
print("=" * 78)
post({"action": "create", "id": P3})
r = post({"action": "setprojectnumber", "id": P3, "newId": "PRJ-A1B-03R"})
check(r.get("ok") is True and r["project"]["id"] == "PRJ-A1B-03R", "rename round-trips",
      str(r)[:160])
check(get({"action": "get", "id": P3}).get("error") == f"Not found: {P3}",
      "old project number no longer resolves")
check(get({"action": "get", "id": "PRJ-A1B-03R"}).get("ok") is True,
      "new project number resolves")
check("already exists" in post({"action": "setprojectnumber", "id": "PRJ-A1B-03R",
                                "newId": P1}).get("error", ""),
      "rename onto an existing id refused")
check("invalid characters" in post({"action": "setprojectnumber", "id": "PRJ-A1B-03R",
                                    "newId": "no way"}).get("error", ""),
      "rename to invalid characters refused")
check(post({"action": "setprojectnumber", "id": P1, "newId": P1}).get("unchanged") is True,
      "same-id rename reports unchanged")

print()
print("=" * 78)
print("RESETSIGNALS / OVERWRITESIGNAL")
print("=" * 78)
doc = get({"action": "get", "id": P1})["project"]
doc["signals"] = {"evm": {"cpi": 0.9}}
doc["signalInputs"] = {"cpi": 0.9, "spi": 0.95}
doc["events"] = list(doc.get("events") or []) + [
    {"event": "signals_extracted", "at": "2026-07-01T00:00:00.000Z"}]
post({"action": "save", "project": doc})
r = post({"action": "overwritesignal", "id": P1, "field": "cpi", "value": 0.85,
          "reason": "manual correction"})
check(r.get("ok") is True and r["from"] == 0.9 and r["to"] == 0.85,
      "overwritesignal reports from/to and persists", str(r)[:160])
check(get({"action": "get", "id": P1})["project"]["signalInputs"]["cpi"] == 0.85,
      "overwritten value read back")
check("No extracted signals" in post({"action": "overwritesignal", "id": P2,
                                      "field": "cpi", "value": 1}).get("error", ""),
      "overwrite with no extracted signals refused")
# THE EVENT LOG IS APPEND-ONLY THROUGH A RESET.
#
# w_resetsignals used to keep only `signals_extracted` and discard every other entry, which made
# it the one write on the platform that removed the record of something having happened. These
# checks are written against COUNTS AND NAMES taken immediately before the call, not against
# constants, so they cannot pass by the fixture happening to be empty.
before_doc = get({"action": "get", "id": P1})["project"]
before_events = list(before_doc.get("events") or [])
before_names = [e.get("event") for e in before_events]
# The precondition that makes everything below non-vacuous: the log must contain entries that are
# NOT signals_extracted, since those are the ones the old code deleted. Asserted, not assumed.
check(len([n for n in before_names if n != "signals_extracted"]) >= 2,
      "precondition: the log carries at least two non-signals_extracted entries to lose",
      str(before_names))

r = post({"action": "resetsignals", "id": P1})
check(r.get("ok") is True and r.get("reset") is True, "resetsignals ok", str(r)[:120])
saved = get({"action": "get", "id": P1})["project"]
check(saved["signals"] == {} and saved["signalInputs"] == {}, "signals cleared")

after_events = list(saved.get("events") or [])
after_names = [e.get("event") for e in after_events]
check(len(after_events) > len(before_events),
      "a reset GROWS the event log; it never shortens it",
      f"{len(before_events)} -> {len(after_events)}")
check(after_names[:len(before_names)] == before_names,
      "every entry that was there before is still there, in order",
      f"{before_names} -> {after_names}")
check(after_names[-1] == "signals_reset",
      "and the reset itself is the entry that was added", str(after_names[-1]))
check(any(e.get("event") == "signals_extracted" for e in saved["events"]),
      "signals_extracted events preserved through reset (docCount source)")

# The reset RECORDS WHAT IT DID. Checked against the values read before the call, so the check
# fails if the handler stops recording them or records the wrong ones.
reset_entry = after_events[-1]
before_inputs = before_doc.get("signalInputs") or {}
check(reset_entry.get("cleared_signal_input_fields") == len(before_inputs),
      "the reset event records how many signalInputs fields it cleared",
      f"recorded {reset_entry.get('cleared_signal_input_fields')}, actually {len(before_inputs)}")
check(reset_entry.get("cleared_signal_input_names") == sorted(before_inputs.keys()),
      "and which ones they were",
      f"{reset_entry.get('cleared_signal_input_names')} vs {sorted(before_inputs.keys())}")
check(len(before_inputs) > 0,
      "precondition: there were signalInputs to clear, so the two checks above mean something",
      str(sorted(before_inputs.keys())))

# A SAVE MAY EXTEND THE EVENT LOG AND MAY NOT SHORTEN OR REWRITE IT.
#
# w_save replaces the stored document with the client's copy, so `events` was whatever the client
# sent. A save with no events key wiped the log; a save with a fabricated list replaced it. Both
# were accepted without a concurrency token.
log_before = [e.get("event") for e in get({"action": "get", "id": P1})["project"]["events"]]
check(len(log_before) >= 3, "precondition: there is a log to lose", str(log_before))

def event_names(resp):
    """Names from a save response, tolerating a missing/!list events key so a handler that drops
    it FAILS the check below instead of raising past it. Injection caught exactly that."""
    evs = ((resp or {}).get("project") or {}).get("events")
    return [e.get("event") for e in evs if isinstance(e, dict)] if isinstance(evs, list) else None


no_events = post({"action": "save", "project": {"id": P1, "name": "A1b One"}})
check(no_events.get("ok") is True, "a save carrying no events key is still accepted")
check(event_names(no_events) == log_before,
      "and it does NOT wipe the stored event log", str(event_names(no_events)))

doc = get({"action": "get", "id": P1})["project"]
doc["events"] = [{"event": "fabricated", "at": "2020-01-01"}]
rewritten = post({"action": "save", "project": doc})
check(event_names(rewritten) == log_before,
      "a save carrying a fabricated shorter log leaves the stored log standing",
      str(event_names(rewritten)))
check("fabricated" not in (event_names(rewritten) or ["fabricated"]),
      "and the fabricated entry is not stored", str(event_names(rewritten)))

# The legacy client legitimately APPENDS (signals.js pushes simulation_run then saves), so an
# extension must still be accepted — otherwise the fix above would be a silent regression.
doc = get({"action": "get", "id": P1})["project"]
doc["events"] = list(doc["events"]) + [{"event": "simulation_run", "at": "2026-08-02T00:00:00Z"}]
extended = post({"action": "save", "project": doc})
check(event_names(extended) == log_before + ["simulation_run"],
      "a genuine client APPEND is still accepted and stored", str(event_names(extended)))

print()
print("=" * 78)
print("SAVEHISTORY / SAVEAUDITRESULT / SAVEPORTFOLIOHEALTH")
print("=" * 78)
r = post({"action": "savehistory", "id": P1, "period": "2026-07",
          "snapshot": {"period": "2026-07", "cpi": 0.85}})
check(r.get("ok") is True and r.get("fileName") == "history_2026-07.json", "savehistory ok",
      str(r)[:120])
hist = get({"action": "gethistory", "id": P1})["history"]
check(any(h.get("cpi") == 0.85 for h in hist), "gethistory returns the stored snapshot")
check("snapshot is required" in post({"action": "savehistory", "id": P1}).get("error", ""),
      "savehistory without snapshot refused")
r = post({"action": "saveauditresult", "id": P1, "auditData": {"reviewType": "monthly"}})
check(r.get("ok") is True and bool(r.get("audit_id")), "saveauditresult ok", str(r)[:120])
check(len(get({"action": "listauditresults", "id": P1})["results"]) >= 1,
      "listauditresults shows the stored row")
r = post({"action": "saveportfoliohealth", "results": {"p1": {"modules": []}},
          "projectCount": 1, "computedAt": "2026-07-31T00:00:00.000Z"})
check(r.get("ok") is True and bool(r.get("savedAt")), "saveportfoliohealth ok", str(r)[:120])
health = get({"action": "getportfoliohealth"})
check(health.get("ok") is True and "p1" in health.get("results", {}),
      "getportfoliohealth returns the stored snapshot at top level")
r2 = post({"action": "saveportfoliohealth", "results": {"p2": {"modules": []}},
           "projectCount": 2, "computedAt": "2026-07-31T01:00:00.000Z"})
health = get({"action": "getportfoliohealth"})
check("p2" in health.get("results", {}) and "p1" not in health.get("results", {}),
      "getportfoliohealth still answers with the LATEST snapshot only")
# APPENDS, NOW. The prior snapshot used to be deleted — the only session.delete in the
# application — before the new one was inserted. It is retained instead: the read behaviour
# above is unchanged (latest wins), but the store itself keeps history the way every other
# record in this module does.
from app.models import ProjectSnapshot as _PS  # noqa: E402
with Session() as _s:
    from app.facade import PORTFOLIO_HEALTH_PERIOD as _PHP
    _rows = _s.scalars(select(_PS).where(_PS.period == _PHP)).all()
    _p1_rows = [r for r in _rows if isinstance(r.snapshot, dict)
               and "p1" in (r.snapshot.get("results") or {})]
    _p2_rows = [r for r in _rows if isinstance(r.snapshot, dict)
               and "p2" in (r.snapshot.get("results") or {})]
    check(len(_rows) >= 2, "the store holds at least two portfolio health rows",
          str(len(_rows)))
    check(bool(_p1_rows), "the p1 snapshot is still IN THE STORE, not deleted",
          str(len(_p1_rows)))
    check(bool(_p2_rows), "and the p2 snapshot is also stored", str(len(_p2_rows)))

print()
print("=" * 78)
print("DEFERRED AND UNKNOWN ACTIONS; PING ADVERTISEMENT")
print("=" * 78)
# `extractsignals` IS NO LONGER IN THIS LIST, and that is the point of the change on 2026-08-04:
# it is dispatched to the real extraction path, so asserting the deferred wording for it would be
# asserting the defect. The seven below have no handler anywhere in server/app — verified against
# every action registry, not assumed — so the refusal is still the accurate answer for them.
for action in ("chat", "analyze", "identifyonly", "audit",
               "portfolioanalyze", "ingestcorpus", "tts"):
    r = post({"action": action, "id": P1})
    check(r.get("error") == f"Action not implemented in this build: {action}",
          f"deferred wording for {action}", str(r)[:120])

# The positive control for the line above. Without this, deleting `extractsignals` from
# DOCUMENT_ACTIONS would put it back in the deferred set and NOTHING here would notice, because
# the loop no longer names it. This asserts it reaches a real handler: the answer must not be the
# deferred sentence and must not be the unknown-action sentence either.
_es = post({"action": "extractsignals", "id": P1})
check(_es.get("error") != "Action not implemented in this build: extractsignals",
      "extractsignals is DISPATCHED, not deferred", str(_es)[:160])
check(_es.get("error") != "Unknown POST action: extractsignals",
      "extractsignals is a known action", str(_es)[:160])
check("Unknown POST action" in post({"action": "definitelynotreal"}).get("error", ""),
      "unknown action wording distinct from deferred")
ping = get({"action": "ping"})
check(len(ping.get("postActionsRegistered", [])) == 10,
      "ping advertises exactly the 10 implemented write actions",
      str(ping.get("postActionsRegistered")))
check(ping.get("portfolioanalyzeRegistered") is False, "portfolioanalyze not advertised")

# The provider-key flags report configuration, read from settings — they were hardcoded false
# and stayed false after the keys were set on Render. Asserted against the environment rather
# than a literal, so this holds whether or not a key is configured where the suite runs.
health = get({"action": "health"})
for field, env_var in (("anthropicKeyPresent", "ANTHROPIC_API_KEY"),
                       ("openaiKeyPresent", "OPENAI_API_KEY")):
    expected = bool((os.environ.get(env_var) or "").strip())
    check(ping.get(field) is expected,
          f"ping {field} tracks {env_var} (expected {expected})", str(ping.get(field)))
    check(health.get(field) is expected,
          f"health {field} tracks {env_var} (expected {expected})", str(health.get(field)))
for secret_var in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
    secret = (os.environ.get(secret_var) or "").strip()
    if secret:
        check(secret not in json.dumps(ping) + json.dumps(health),
              f"{secret_var} value never appears in a health or ping body")

print()
print("=" * 78)
print("THE FACADE FAILS CLOSED: no session, no write")
print("=" * 78)
# guard_project_write used to return None — allow — when the caller presented no session token,
# so an unauthenticated POST could write to any project. Every write action is checked here with
# session_token explicitly set to None, which `post` turns into a genuinely tokenless request.
ADMIN = "a1b-regress-admin"
with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="PM-000", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    s.commit()
admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]

# A project the anonymous caller will be aimed at, and a name to prove it was not changed.
GUARDED = "PRJ-A1B-GUARDED"
RENAME_TARGET = "PRJ-A1B-RENAMEME"
post({"action": "create", "id": GUARDED, "name": "Untouched"})
post({"action": "create", "id": RENAME_TARGET, "name": "Rename target"})
post({"action": "save", "project": {**get({"action": "get", "id": GUARDED})["project"],
                                    "signalInputs": {"cpi": 1.0}}})
before = get({"action": "get", "id": GUARDED})["project"]
check(before.get("name") == "Untouched" and (before.get("signalInputs") or {}).get("cpi") == 1.0,
      "precondition: the target project exists, is named, and carries a signal to overwrite",
      str(before.get("name")))

ANON_WRITES = [
    ("create", {"id": "PRJ-A1B-ANON-NEW", "name": "anon"}),
    ("save", {"project": dict(before, name="RENAMED BY ANON")}),
    ("archive", {"id": GUARDED}),
    ("restore", {"id": GUARDED}),
    # Aimed at its OWN target: if the guard is removed this rename SUCCEEDS, and pointing it at
    # GUARDED would move that project out from under every probe after it, turning their honest
    # refusals into "Project not found" and hiding what the injection is meant to show.
    ("setprojectnumber", {"id": RENAME_TARGET, "newId": "PRJ-A1B-ANON-RENAMED"}),
    ("resetsignals", {"id": GUARDED}),
    ("overwritesignal", {"id": GUARDED, "field": "cpi", "value": 0.01}),
    ("savehistory", {"id": GUARDED, "period": "2026-07", "snapshot": {"anon": True}}),
    ("saveauditresult", {"id": GUARDED, "auditData": {"name": "anon.json"}}),
    ("saveportfoliohealth", {"results": {"anon": 1}, "projectCount": 99}),
]
for _action, _body in ANON_WRITES:
    r = post(dict(_body, action=_action, session_token=None))
    check(r.get("ok") is False and "not authorized" in (r.get("error") or ""),
          f"unauthenticated {_action} is refused", str(r)[:110])

# The refusals must have changed nothing. Read back independently rather than trusting ok:false.
# `or {}` so a project the fault renamed or destroyed makes these checks FAIL rather than raise —
# a suite that dies prints no RESULT line and reads as clean, which is how the last vacuous check
# survived a whole injection pass.
after = get({"action": "get", "id": GUARDED}).get("project") or {}
check(after.get("name") == "Untouched", "the anonymous writes changed nothing: name intact",
      str(after.get("name")))
check((after.get("signalInputs") or {}).get("cpi") == 1.0,
      "signal intact", str(after.get("signalInputs")))
check(after.get("archived") in (None, False), "not archived", str(after.get("archived")))
check((get({"action": "get", "id": RENAME_TARGET}).get("project") or {}).get("id")
      == RENAME_TARGET, "and the rename target still answers to its own id",
      str(get({"action": "get", "id": RENAME_TARGET}).get("error"))[:60])
check(get({"action": "get", "id": "PRJ-A1B-ANON-NEW"}).get("ok") is not True,
      "and the anonymous create left no project behind")

# A token that does not resolve is refused too, on a project with NO membership rows — the case
# that used to skip resolve_caller entirely because the membership check came first.
r = post({"action": "save", "session_token": "not-a-token",
          "project": get({"action": "get", "id": GUARDED}).get("project") or {"id": GUARDED}})
check(r.get("ok") is False, "a malformed session token is refused on an unmembered project",
      str(r)[:160])

# B8 authorisation still applies on top: a valid session that is not the project's PM is refused.
# The document is captured BEFORE the member is added, because adding one also closes the project
# to this suite's session for READS — which is the read guard doing its job and is asserted below.
doc = get({"action": "get", "id": P1})["project"]
member = post({"action": "adminparticipantcreate", "session_token": admin})
member_tok = post({"action": "researchlogin",
                   "access_token": member["access_token"]})["session_token"]
# This suite's session created P1 and therefore holds PM on it — creation writes the membership
# row in the same transaction as of 2026-08-02. Hand PM over so the checks below exercise a
# non-PM, which is what they are about.
_creator_row = next(m for m in post({"action": "adminmemberlist", "session_token": admin,
                                     "id": P1})["members"] if m["user_key"] == WRITER_ID)
_handover = post({"action": "adminmemberrevoke", "session_token": admin,
                  "member_id": _creator_row["member_id"]})
check(_handover.get("ok") is True, "the creator's PM row can be revoked to hand the project on",
      str(_handover)[:120])
_add = post({"action": "adminmemberadd", "session_token": admin, "id": P1,
             "participant_id": member["participant_id"], "project_role": "PM"})
check(_add.get("ok") is True, "and a new PM is then accepted", str(_add)[:120])
doc["name"] = "non-PM write on a membered project"
r = post({"action": "save", "project": doc})
check(r.get("ok") is False and "only the project's PM" in (r.get("error") or ""),
      "an authenticated non-PM is still refused on a membered project", str(r)[:160])
check((get({"action": "get", "id": P1}, ).get("project") or {}).get("name")
      != "non-PM write on a membered project", "and that write did not land either")

# READS ARE AUTHORISED TOO, as of 2026-08-02. P1 now has a PM who is not this suite's session, so
# this suite must no longer be able to read it — and the PM must still be able to.
r = get({"action": "get", "id": P1})
check(r.get("ok") is False and "not a member" in (r.get("error") or ""),
      "a non-member is refused a READ of a membered project", str(r)[:120])
check("project" not in r, "and the refusal carries no project payload at all", str(sorted(r)))
r = client.get("/exec", params={"action": "get", "id": P1},
               headers={"Authorization": "Bearer " + member_tok}).json()
check(r.get("ok") is True and (r.get("project") or {}).get("id") == P1,
      "while the project's own PM reads it normally", str(r)[:120])
# Collections are FILTERED rather than refused: the membered project drops out of this session's
# list, and the projects it does own stay.
listed = [p["id"] for p in (get({"action": "list"}).get("projects") or [])]
check(P1 not in listed, "the membered project is filtered out of a non-member's list",
      str(listed)[:120])
check(GUARDED in listed, "and the caller's own projects are still listed",
      str(listed)[:120])

print()
print("=" * 78)
print("A PROJECT WITH NO MEMBERSHIP ROWS AT ALL IS REACHABLE BY NOBODY")
print("=" * 78)
# THE ARM CLOSED ON 2026-08-02, and it needs its own fixture because nothing can produce this
# state any more: both creation paths write the owner's PM row in the same transaction. So the
# row is inserted directly, which is exactly how the eight orphans in the development database
# came to exist — seeded straight into `projects` as transition targets, never created through
# any action.
#
# Every other "unmembered" check in this suite is really a NON-MEMBER check against a project
# that does have members. That is a different guard arm, it passed before this change, and a
# fault reopening the unmembered arm leaves it green. This block is the one that goes red.
ORPHAN = "PRJ-A1B-ORPHAN"
with main.SessionFactory() as s:
    if s.scalar(select(Project).where(Project.legacy_id == ORPHAN)) is None:
        s.add(Project(legacy_id=ORPHAN, doc={"id": ORPHAN, "name": "Orphan, no members ever"}))
        s.commit()
with main.SessionFactory() as s:
    from app.research_models import ProjectMember
    orphan = s.scalar(select(Project).where(Project.legacy_id == ORPHAN))
    rows = s.scalars(select(ProjectMember).where(ProjectMember.project_id == orphan.id)).all()
check(len(rows) == 0, "the fixture really has no membership rows, revoked ones included",
      f"{len(rows)} rows")

r = get({"action": "get", "id": ORPHAN})
check(r.get("ok") is False and "not a member" in (r.get("error") or ""),
      "an authenticated caller is refused a READ of a project with no members", str(r)[:130])
check("project" not in r, "and that refusal carries no project payload", str(sorted(r)))

r = post({"action": "archive", "id": ORPHAN})
# archive/restore are open to either project role (project-delete-s5s90m), so a caller with NO
# membership row at all gets the membership-required wording, not the PM-only wording used by
# every other project write.
check(r.get("ok") is False and "only a project member" in (r.get("error") or ""),
      "and refused a WRITE to it", str(r)[:130])
with main.SessionFactory() as s:
    still = s.scalar(select(Project).where(Project.legacy_id == ORPHAN))
check(still is not None and not still.archived, "and that write did not land",
      str(bool(still and still.archived)))

listed = [p["id"] for p in (get({"action": "list"}).get("projects") or [])]
check(ORPHAN not in listed, "and it does not appear in the portfolio list either",
      str(listed)[:130])

print()
print("=" * 78)
passed = sum(1 for ok, _, _ in results if ok)
print(f"RESULT: {passed}/{len(results)} checks passed")
print("=" * 78)
sys.exit(0 if passed == len(results) else 1)
