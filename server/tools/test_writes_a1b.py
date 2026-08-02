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


def post(payload: dict) -> dict:
    r = client.post("/exec", content=json.dumps(payload), headers={"Content-Type": "text/plain"})
    assert r.status_code == 200, f"contract violation: HTTP {r.status_code}"
    return r.json()


def get(params: dict) -> dict:
    r = client.get("/exec", params=params)
    assert r.status_code == 200
    return r.json()


P1, P2, P3 = "PRJ-A1B-01", "PRJ-A1B-02", "PRJ-A1B-03"

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
      "portfolio health snapshot is a replaced singleton")

print()
print("=" * 78)
print("DEFERRED AND UNKNOWN ACTIONS; PING ADVERTISEMENT")
print("=" * 78)
for action in ("chat", "analyze", "extractsignals", "identifyonly", "audit",
               "portfolioanalyze", "ingestcorpus", "tts"):
    r = post({"action": action, "id": P1})
    check(r.get("error") == f"Action not implemented in this build: {action}",
          f"deferred wording for {action}", str(r)[:120])
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
print("B8: sessionless facade writes are unchanged, even on a membered project")
print("=" * 78)
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
member = post({"action": "adminparticipantcreate", "session_token": admin})
post({"action": "adminmemberadd", "session_token": admin, "id": P1,
      "participant_id": member["participant_id"], "project_role": "PM"})
doc = get({"action": "get", "id": P1})["project"]
doc["name"] = "sessionless write on membered project"
r = post({"action": "save", "project": doc})
check(r.get("ok") is True, "sessionless save still works on a membered project", str(r)[:160])
doc = get({"action": "get", "id": P1})["project"]
r = post({"action": "save", "session_token": "not-a-token", "id": P1, "project": doc})
check(r.get("ok") is False, "a malformed session token on a membered project's write is refused,"
      " not silently treated as sessionless", str(r)[:160])

print()
print("=" * 78)
passed = sum(1 for ok, _, _ in results if ok)
print(f"RESULT: {passed}/{len(results)} checks passed")
print("=" * 78)
sys.exit(0 if passed == len(results) else 1)
