#!/usr/bin/env python3
"""
RUN 48. THE PERIOD THE PROJECT DETAIL PAGE OPENS ON, DRIVEN THROUGH THE REAL ROUTES.

WHAT THIS SUITE EXISTS TO PROTECT. `primeAndRefresh` in assets/js/detail.js read the stored
result back with a hard-coded `period: 1`. Every panel on the project detail page then held
that row -- the key drivers, the abstention reasons, `recommendation_basis` and the Run 47
disagreement findings -- so on a project whose current period is not 1 the whole page showed
period 1 and said nothing about it. The owner's ruling 1 of 2026-08-22: the page shows the
LATEST PERIOD THAT HAS DOCUMENTS AND HAS BEEN COMPUTED FROM THEM. Not period 1, and not the
latest period with documents alone.

THE RULES THIS SUITE HOLDS ITSELF TO.

  * EVERY EXPECTED PERIOD IS A LITERAL WRITTEN HERE, chosen when the fixture was built. Nothing
    is read back out of `_latest_computed_period` and compared with itself, and no generated
    output validates itself against its own generator.
  * NOTHING IS ASSUMED ABOUT PERIOD NUMBERING. The fixtures include a project whose computed
    periods have a hole in them (1 and 4, with 2 and 3 absent), a project whose latest period
    holds documents that have never been computed, and a project computed at period 48. A
    determination that assumed contiguity, or that the highest period number has results, or
    any maximum count, fails here rather than passing quietly.
  * A FIXTURE IS BUILT THROUGH THE ROUTES THE APPLICATION ACTUALLY TAKES: `researchlogin`,
    `adminparticipantcreate`, `adminmemberadd`, `projectupload`, `projectcompute`,
    `projectperiods`, `projectresults`. Extraction is stubbed, which is the one substitution
    every suite in this repository makes; everything downstream of it is the production path.

Run:
    DATABASE_URL=... SESSION_SECRET=... python tools/test_run48_current_period.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

import app.main as main  # noqa: E402
from app.documents import set_extractor_override  # noqa: E402
from app.extraction_client import StubExtractor  # noqa: E402
from app.models import Project  # noqa: E402
from app.research_identity import hash_access_token  # noqa: E402
from app.research_models import (  # noqa: E402
    Assignment, Decision, Participant, Scenario,
)
from app.research_membership import ProjectMember  # noqa: E402
from app.simulation.registry import (  # noqa: E402
    CORE_VOTING_MODULES, registry_index, service_index,
)

ROOT = pathlib.Path(__file__).resolve().parents[2]

#: RUN 54. THE COMMIT THE DEEP-DIVE SURFACE WAS DELETED FROM, PINNED. It must NOT be written as
#: `HEAD~1`: that was true only while the deletion was the last commit, and it walked back one
#: commit per later commit until it pointed at a tree where the file was already gone, turning a
#: real non-vacuity proof into a false one. Caught by running the full suite pass, not by reading.
RUN54_PREDELETION_COMMIT = "bf36ef6"

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


ADMIN = "run48-admin-token"

# ------------------------------------------------------------------------ the fixture projects
#
# Each name states what it is FOR, and the expected period beside it is a literal chosen here.
TWO = "PRJ-R48-TWO"        # computed at 1 and 2                        -> opens on 2
DOCS_ONLY = "PRJ-R48-DOCS"  # computed at 1 and 2, documents at 3        -> opens on 2
FOUR = "PRJ-R48-FOUR"      # computed at 1, 2, 3 and 4                  -> opens on 4
GAP = "PRJ-R48-GAP"        # computed at 1 and 4, nothing at 2 or 3     -> opens on 4
HIGH = "PRJ-R48-HIGH"      # computed at 48                             -> opens on 48
NONE_ = "PRJ-R48-NONE"     # documents at 1, never computed             -> opens on nothing
#: The research-chain probe of section 8. Its PM is a RESEARCH participant, because an
#: operational account structurally cannot hold an assignment (consent is refused at source).
RESEARCH = "PRJ-R48-RESEARCH"

#: project -> the period the page must open on. LITERALS, not derived.
EXPECTED: dict[str, int | None] = {
    TWO: 2, DOCS_ONLY: 2, FOUR: 4, GAP: 4, HIGH: 48, NONE_: None,
}

#: The research probe project is created and computed alongside the six, but it is NOT part of
#: the EXPECTED table: what it establishes is section 8's question, not ruling 1's.
RESEARCH_PERIODS = (1, 2, 3, 4)

#: project -> the periods documents are uploaded into.
UPLOADS: dict[str, tuple[int, ...]] = {
    TWO: (1, 2),
    DOCS_ONLY: (1, 2, 3),
    FOUR: (1, 2, 3, 4),
    GAP: (1, 4),
    HIGH: (48,),
    NONE_: (1,),
    RESEARCH: RESEARCH_PERIODS,
}

#: project -> the periods that are actually COMPUTED. The difference between this and UPLOADS
#: is the whole of ruling 1: a period with documents and no computed result is not selected.
COMPUTE: dict[str, tuple[int, ...]] = {
    TWO: (1, 2),
    DOCS_ONLY: (1, 2),
    FOUR: (1, 2, 3, 4),
    GAP: (1, 4),
    HIGH: (48,),
    NONE_: (),
    RESEARCH: RESEARCH_PERIODS,
}

BAC = 4_000_000


def period_end(period: int) -> str:
    """A stated ending date, one month apart, generated for any period number."""
    year = 2026 + (period - 1) // 12
    month = ((period - 1) % 12) + 1
    return f"{year:04d}-{month:02d}-28"


def extraction(period: int) -> dict:
    """
    A monthly report stating enough for the period to compute to a banded result.

    RUN 75, A PREMISE FAULT IN THIS FIXTURE, FOUND BY THE RUN 75 CHANGE AND CORRECTED HERE.

    Three of the five figures were named `earned_value_to_date`, `actual_cost_to_date` and
    `planned_value_to_date`. THE MONTHLY REPORT'S EXTRACTION CONTRACT ASKS FOR NONE OF THEM:
    `extraction_fields_for("monthly_report")` requests `earned_value`, `actual_cost` and
    `planned_value` (`extraction_fields.py`), so every one of those three was dropped at the
    door, no observation was stored for them, and every project this file built computed to a
    live row carrying ZERO module results.

    The docstring said "enough to compute to a banded result" and it was not true. The
    assertions above it -- highest-number-not-assumed, contiguity-not-assumed, no-maximum,
    supersession -- were therefore all being made over rows with nothing in them, which is
    EXACTLY the shape Run 75 was sent to fix: a row existing taken for a result existing. The
    pin passed 56/56 because `_computed_periods` also could not tell the two apart.

    Only the three names are corrected. No assertion is added, removed or relaxed, and every
    check above still asks the same question -- it now asks it of rows that really hold results.
    """
    return {
        "budget_at_completion": BAC,
        "earned_value": 100_000 * period,
        "actual_cost": 105_000 * period,
        "planned_value": 102_000 * period,
        "report_date": period_end(period),
        "document_date": period_end(period),
    }


def doc_bytes(project: str, period: int) -> bytes:
    return f"%PDF-1.4 RUN48 {project} P{period}\n".encode()


RECORDED: dict[str, tuple[str, dict]] = {
    hashlib.sha256(doc_bytes(_p, _per)).hexdigest(): ("monthly_report", extraction(_per))
    for _p, _pers in UPLOADS.items() for _per in _pers
}
set_extractor_override(StubExtractor(RECORDED))

with Session() as s:
    row = s.scalar(select(Participant).where(Participant.role == "ResearchAdmin"))
    if row is None:
        s.add(Participant(pseudonymous_code="R48-ADMIN", role="ResearchAdmin",
                          access_token_hash=hash_access_token(ADMIN)))
    else:
        row.access_token_hash = hash_access_token(ADMIN)
    for legacy in list(EXPECTED) + [RESEARCH]:
        if s.scalar(select(Project).where(Project.legacy_id == legacy)) is None:
            s.add(Project(legacy_id=legacy,
                          doc={"id": legacy, "name": legacy, "signals": {}, "events": []}))
    s.commit()

admin = post({"action": "researchlogin", "access_token": ADMIN})["session_token"]
created = post({"action": "adminparticipantcreate", "session_token": admin,
                "pseudonymous_code": "R48-PM", "role": "Participant",
                "account_type": "operational"})
pm = post({"action": "researchlogin", "access_token": created["access_token"]})["session_token"]
for legacy in EXPECTED:
    post({"action": "adminmemberadd", "session_token": admin, "id": legacy,
          "participant_id": created["participant_id"], "project_role": "PM"})

# THE RESEARCH PM, for section 8. A research account, consented through the real route, because
# an operational account cannot hold an assignment at all: `a_consentgrant` refuses it at source
# and the consent gate then refuses every research write for it.
rcreated = post({"action": "adminparticipantcreate", "session_token": admin,
                 "pseudonymous_code": "R48-RPM", "role": "Participant",
                 "account_type": "research"})
rpm = post({"action": "researchlogin", "access_token": rcreated["access_token"]})["session_token"]
_consent = post({"action": "consentgrant", "session_token": rpm,
                 "consent_version": "run48-probe-consent-v1"})
assert _consent.get("ok") is True, str(_consent)[:300]
post({"action": "adminmemberadd", "session_token": admin, "id": RESEARCH,
      "participant_id": rcreated["participant_id"], "project_role": "PM"})

for _legacy, _periods in UPLOADS.items():
    _tok = rpm if _legacy == RESEARCH else pm
    for _per in _periods:
        r = post({"action": "projectupload", "session_token": _tok, "id": _legacy,
                  "period": _per, "period_end": period_end(_per),
                  "documents": [{"filename": f"{_legacy}-p{_per}.pdf",
                                 "mimeType": "application/pdf",
                                 "dataBase64": b64(doc_bytes(_legacy, _per))}]})
        assert r.get("ok") is True, f"{_legacy} p{_per}: {str(r)[:300]}"

for _legacy, _periods in COMPUTE.items():
    _tok = rpm if _legacy == RESEARCH else pm
    for _per in _periods:
        r = post({"action": "projectcompute", "session_token": _tok, "id": _legacy,
                  "period": _per})
        assert r.get("ok") is True, f"compute {_legacy} p{_per}: {str(r)[:300]}"


def periods_view(legacy: str) -> dict:
    r = post({"action": "projectperiods", "session_token": pm, "id": legacy})
    assert r.get("ok") is True, str(r)[:300]
    return r


DETAIL = (ROOT / "assets" / "js" / "detail.js").read_text(encoding="utf-8")
# RUN 54. `assets/js/deepdive.js` was DELETED on the owner's ruling at section 8 of the Run 54
# order. Every Run-48 check below asserted a property of ITS TEXT -- that its panel table held
# category KEYS rather than the retired "Cat N" labels, and that a panel's label came from the
# loaded taxonomy. Those checks existed to keep a retired identifier scheme out of a rendered
# surface. THE SURFACE IS GONE, so they are asserted against the file's LAST COMMITTED BYTES,
# which is the strongest thing that can still be said about a deleted file, and the deletion
# itself is asserted separately. Reading a PINNED commit rather than the working tree is the same
# discipline the participant-package chain uses for every predecessor record.
_DEEPDIVE_REL = "assets/js/deepdive.js"
_DEEPDIVE_LAST = subprocess.run(
    ["git", "-C", str(ROOT), "show", f"{RUN54_PREDELETION_COMMIT}:{_DEEPDIVE_REL}"], capture_output=True)
DEEPDIVE = _DEEPDIVE_LAST.stdout.decode("utf-8") if _DEEPDIVE_LAST.returncode == 0 else ""
CHARTS3D = (ROOT / "assets" / "js" / "charts3d.js").read_text(encoding="utf-8")

try:
    print("=" * 78)
    print("1. THE PERIOD THE PAGE OPENS ON, DERIVED THROUGH THE REAL ROUTE (S6.1-S6.6)")
    print("=" * 78)

    for _legacy, _want in EXPECTED.items():
        _got = periods_view(_legacy)["latest_computed_period"]
        check(_got == _want,
              f"{_legacy}: the page opens on {_want!r}, derived and not assumed", str(_got))

    print()
    print("=" * 78)
    print("2. THE THREE ASSUMPTIONS RULING 1 FORBIDS, EACH REFUTED BY A FIXTURE")
    print("=" * 78)

    _docs = periods_view(DOCS_ONLY)
    _doc_periods = sorted(r["period"] for r in _docs["periods"])
    check(_doc_periods == [1, 2, 3],
          "the documents-only project holds documents in periods 1, 2 and 3", str(_doc_periods))
    check(_docs["next_period"] == 4,
          "and its highest period holding a document is 3", str(_docs["next_period"]))
    check(_docs["latest_computed_period"] == 2,
          "yet the page opens on 2: THE HIGHEST PERIOD NUMBER IS NOT ASSUMED TO HAVE RESULTS",
          str(_docs["latest_computed_period"]))
    check(_docs["computed_periods"] == [1, 2],
          "and period 3 is served as NOT computed, so a reader can tell a period that holds "
          "documents from one that has been computed from them",
          f'documents {_doc_periods} vs computed {_docs["computed_periods"]}')

    _gap = periods_view(GAP)
    check(_gap["computed_periods"] == [1, 4],
          "the gap project's computed periods are 1 and 4 with a hole between them",
          str(_gap["computed_periods"]))
    check(_gap["latest_computed_period"] == 4,
          "and the page opens on 4: CONTIGUITY IS NOT ASSUMED",
          str(_gap["latest_computed_period"]))

    _high = periods_view(HIGH)
    check(_high["computed_periods"] == [48],
          "the high project is computed at period 48 and nowhere else",
          str(_high["computed_periods"]))
    check(_high["latest_computed_period"] == 48,
          "and the page opens on 48: NO MAXIMUM PERIOD COUNT IS ASSUMED",
          str(_high["latest_computed_period"]))

    _none = periods_view(NONE_)
    check(_none["latest_computed_period"] is None,
          "a project with no computed result in any period returns null, not 1",
          str(_none["latest_computed_period"]))
    check(_none["computed_periods"] == [] and _none["ok"] is True,
          "and it returns cleanly rather than erroring, so the page keeps its empty state",
          str(_none["computed_periods"]))

    print()
    print("=" * 78)
    print("3. THE SELECTED PERIOD IS THE ONE THE ROW COMES FROM (S6.1-S6.5)")
    print("=" * 78)

    for _legacy, _want in EXPECTED.items():
        if _want is None:
            _r = post({"action": "projectresults", "session_token": pm, "id": _legacy,
                       "period": 1})
            check(_r.get("ok") is not True,
                  f"{_legacy}: there is no row to read at all, in any period", str(_r)[:120])
            continue
        _r = post({"action": "projectresults", "session_token": pm, "id": _legacy,
                   "period": _want})
        check(_r.get("ok") is True and _r["result"].get("period") == _want,
              f"{_legacy}: the row served for the selected period is period {_want}'s own row",
              str(_r.get("result", {}).get("period")))

    # AND THE OLD BEHAVIOUR IS DEMONSTRABLY DIFFERENT. Period 1's row exists on four of the
    # fixtures and is NOT the row the page must now open on. Without this the suite could pass
    # against a determination that still returned 1.
    for _legacy in (TWO, DOCS_ONLY, FOUR, GAP):
        _r1 = post({"action": "projectresults", "session_token": pm, "id": _legacy, "period": 1})
        check(_r1.get("ok") is True and _r1["result"]["period"] == 1
              and EXPECTED[_legacy] != 1,
              f"{_legacy}: period 1 still has a row, and it is NOT the one the page opens on, "
              f"so a determination that returned 1 would fail here", str(_r1)[:120])

    print()
    print("=" * 78)
    print("4. A SUPERSEDED RESULT IS NOT A COMPUTED PERIOD")
    print("=" * 78)

    # Recomputing period 4 of FOUR supersedes its row and writes a live one. The determination
    # must still read 4, and the count of live computed periods must not grow.
    _before = periods_view(FOUR)["computed_periods"]
    _rc = post({"action": "projectcompute", "session_token": pm, "id": FOUR, "period": 4})
    check(_rc.get("ok") is True, "period 4 recomputes through the real route", str(_rc)[:160])
    _after = periods_view(FOUR)
    check(_after["computed_periods"] == _before == [1, 2, 3, 4],
          "a superseded row adds no period: the live results are still exactly 1, 2, 3 and 4",
          f"{_before} -> {_after['computed_periods']}")
    check(_after["latest_computed_period"] == 4,
          "and the page still opens on 4", str(_after["latest_computed_period"]))

    print()
    print("=" * 78)
    print("5. THE PAGE ITSELF READS THE DERIVED PERIOD, NOT A LITERAL (S6.8)")
    print("=" * 78)

    check("period: 1" not in DETAIL,
          "assets/js/detail.js carries NO `period: 1` literal anywhere",
          str([ln for ln in DETAIL.splitlines() if "period: 1" in ln])[:200])
    check('{ action: "projectperiods", id: id, session_token: tok }' in DETAIL,
          "primeAndRefresh asks the server which periods have been computed")
    check('{ action: "projectresults", id: id, period: period, session_token: tok }' in DETAIL,
          "and reads the stored row back for the period it derived, not for a constant")
    check("const period = await currentPeriod(id, tok);" in DETAIL
          and "if (period === null) return;" in DETAIL,
          "and a project with no computed period returns before any results call, so the "
          "existing empty state stands and no new one is invented")
    # THE SWEEP, over every read-path period literal in the file, executed here rather than
    # asserted from a report.
    _literals = [ln.strip() for ln in DETAIL.splitlines()
                 if re.search(r"period\s*[:=]\s*\d+\b", ln) and not ln.strip().startswith("//")]
    check(not _literals,
          "and no other numeric period literal survives on a read path in this file",
          str(_literals)[:300])

    print()
    print("=" * 78)
    print("6. THE LIVE NAMING INSTANCES ARE CORRECTED (S6.11, S6.12)")
    print("=" * 78)

    # RUN 51, RULINGS 5 AND 6. Run 48 separated the panel LABEL map from the panel BUCKET map so
    # that the text could be corrected without moving a panel. Run 51 replaced BOTH with ONE
    # table of category KEYS, from which the label and the bucket are derived through the loaded
    # taxonomy: the label a participant reads is now the category's own NAME and is not in this
    # file at all, which is a stronger form of the property Run 48 asserted. Every check below is
    # restated against that table. None is deleted.
    _map = DEEPDIVE[DEEPDIVE.index("const CAT_KEY_FROM_MODULE"):
                    DEEPDIVE.index("function projectCatList")]
    check(not re.search(r'"Cat\s', _map),
          "deepdive.js's panel table no longer maps a module number to a retired label",
          _map[:200])
    check('"01": "A1"' in _map and '"19": "B3"' in _map,
          "its values are CATEGORY KEYS in the current taxonomy, keyed on the legacy module "
          "numbers the call sites pass, which are matched against and never displayed")
    check('"Cat " + key' not in DEEPDIVE,
          "and the fallback no longer builds a label out of the retired scheme",
          str([ln for ln in DEEPDIVE.splitlines() if '"Cat " + key' in ln])[:200])
    check('return (cat && cat.name) || "Signal Analysis";' in DEEPDIVE,
          "a panel is labelled with its category's own name, read from the loaded taxonomy, and "
          "an unmapped module is described by its purpose and nothing else")
    check("Synthesis\\n(Cat 6)" not in CHARTS3D and "Signal\\nSynthesis" in CHARTS3D,
          "charts3d.js labels the synthesis node by its purpose")
    check('return c.name + ": " + c.status + worstDesc;' in DETAIL
          and 'c.num + " " + c.name + ": " + c.status' not in DETAIL,
          "detail.js sends the brief's model a category name and status with no identifier")
    check("const BRIEF_CAT_LABEL" not in DETAIL,
          "BRIEF_CAT_LABEL is deleted: no declaration survives")
    check("BRIEF_CAT_LABEL" not in DETAIL,
          "and the name does not appear in the file at all, not even in the comment that "
          "records the deletion",
          str(len(re.findall(r"BRIEF_CAT_LABEL", DETAIL))))
    _js = sorted((ROOT / "assets" / "js").glob("*.js"))
    _carriers = [p.name for p in _js if "BRIEF_CAT_LABEL" in p.read_text(encoding="utf-8")]
    check(not _carriers,
          "and no served JavaScript file in the tree carries the constant", str(_carriers))

    # RUN 51, RULING 5. Run 48 asserted that correcting the LABEL moved no panel, by pinning the
    # bucket numbers as literals. Ruling 5 ORDERS panels to move -- to the category their module
    # belongs to in the CURRENT taxonomy -- and ruling 6 orders the bucket to be derived rather
    # than written as a literal at all. The property Run 48 was protecting survives in a stronger
    # form: the label and the bucket now come from ONE table through the loaded taxonomy, so
    # correcting the text cannot move a panel because the text is not the source of either.
    check("CAT_NUM_FROM_MODULE" not in DEEPDIVE
          and '"01": "A1", "02": "A1"' in DEEPDIVE and '"09": "B1"' in DEEPDIVE
          and '"19": "B3"' in DEEPDIVE,
          "the panel bucket is derived from the same category key the label is, so they cannot "
          "disagree and correcting the text cannot move a panel; and the retired numbers the "
          "old literal map held are gone from the file")

    print()
    print("=" * 78)
    print("7. THE COMMENT MARKERS ARE UNTOUCHED (S6.13)")
    print("=" * 78)

    for _rel, _needle in (
            ("assets/js/app.js", 'Cat 8 (Governance, ex-Cat 9) is open by'),
            ("assets/js/categories.js", 'True for the Portfolio Health suite (ex-"Cat 8")'),
            ("assets/js/neural_flow.js", 'Every document row the old array sent to "Cat 8"'),
            ("assets/js/taxonomy.js", "Cat 8")):
        _txt = (ROOT / _rel).read_text(encoding="utf-8")
        check(_needle in _txt,
              f"{_rel}: the comment recording why a thing moved is still there",
              _needle)
    # RUN 54. assets/js/deepdive.js carried a sixth marker, 'Portfolio Health (ex-"Cat 8") is
    # portfolio-scale'. The file is DELETED, so the marker is asserted where it now lives -- in
    # the last committed bytes -- and the deletion is asserted beside it. NON-VACUOUS: the file
    # existed at the prior commit, proved against git.
    check(_DEEPDIVE_LAST.returncode == 0
          and 'Portfolio Health (ex-"Cat 8") is portfolio-scale' in DEEPDIVE
          and not (ROOT / _DEEPDIVE_REL).exists(),
          "assets/js/deepdive.js: the comment was there right up to the deletion, and the file "
          "is now gone",
          f"existed_at_bf36ef6={_DEEPDIVE_LAST.returncode == 0} "
          f"exists_now={(ROOT / _DEEPDIVE_REL).exists()}")

    print()
    print("=" * 78)
    print("8. WHAT THE decision-ui.js PERIOD LITERALS ACTUALLY GOVERN, ESTABLISHED BY EXECUTION")
    print("=" * 78)
    #
    # THE SECTION 5.1 SWEEP FOUND THREE MORE `period: 1` LITERALS, all in assets/js/decision-ui.js
    # (:345 `projectresults`, :346 `projectuploadstatus`, :545 `projectresults`). That file is
    # SEQUENCE-BEARING, and Run 48 is authorised to move deepdive.js and no other, so they are
    # reported rather than corrected. What they GOVERN is established here by execution rather
    # than assumed from their names.
    #
    # THE FINDING: on a project that is a scenario's evidence package -- which is the only kind
    # of project decision-ui.js ever addresses, since it reads `STATE.server.evidence_project_id`
    # -- `documents._resolve_period` IGNORES THE PAYLOAD ENTIRELY and derives the period from the
    # participant's assignment. The literal is therefore INERT on that surface: it cannot select
    # period 1, and it cannot make Run 48's detail-page fix ineffective, because the detail page
    # is a different surface reading a different route call.
    _R = RESEARCH                  # computed at 1, 2, 3 and 4, with a RESEARCH participant as PM
    with Session() as _s:
        _proj = _s.scalar(select(Project).where(Project.legacy_id == _R))
        _pm_member = _s.scalar(select(ProjectMember).where(
            ProjectMember.project_id == _proj.id, ProjectMember.project_role == "PM"))
        _sc = Scenario(scenario_version="run48-probe", evidence_package_id=_R,
                       period_count=4, status="frozen")
        _s.add(_sc)
        _s.flush()
        _asg = Assignment(participant_id=_pm_member.user_key, scenario_id=_sc.scenario_id,
                          sequence_number=1, status="in_progress")
        _s.add(_asg)
        _s.flush()
        # A decision row at P3 that has not been finally submitted. `current_period` then reads
        # P3, which is neither 1 nor the latest computed period 4 -- so the two possible wrong
        # answers are both distinguishable from the right one.
        _s.add(Decision(assignment_id=_asg.assignment_id, period="P3"))
        _s.commit()

    _r1 = post({"action": "projectresults", "session_token": rpm, "id": _R, "period": 1})
    check(_r1.get("ok") is True and _r1.get("result", {}).get("period") == 3,
          "a research project SERVES PERIOD 3 for a request that states period 1: the route "
          "derives the period from the assignment and the payload literal is ignored entirely",
          str(_r1)[:200])
    _u1 = post({"action": "projectuploadstatus", "session_token": rpm, "id": _R, "period": 1})
    check(_u1.get("ok") is True and _u1.get("period") == 3,
          "and projectuploadstatus answers for period 3 on the same stated period 1, so both "
          "decision-ui.js call sites are governed by the derived period, not by their literal",
          str(_u1)[:200])
    _r9 = post({"action": "projectresults", "session_token": rpm, "id": _R, "period": 4})
    check(_r9.get("ok") is True and _r9.get("result", {}).get("period") == 3,
          "and stating period 4 is ignored in the same way, which is what makes this a "
          "server-derived period rather than a default",
          str(_r9)[:200])
    # AND THE OPERATIONAL CASE, which is the one Run 48 fixes: with no assignment the payload
    # governs, so a hard-coded 1 there really does pin the page to period 1.
    _r2 = post({"action": "projectresults", "session_token": pm, "id": TWO, "period": 1})
    check(_r2.get("ok") is True and _r2["result"]["period"] == 1,
          "on an OPERATIONAL project the stated period governs, which is why the detail page's "
          "literal pinned it to period 1 and why removing it was the fix",
          str(_r2.get("result", {}).get("period")))

    print()
    print("=" * 78)
    print("9. THE STANDING POPULATION GUARANTEES, DERIVED (S6.14, S6.15)")
    print("=" * 78)

    check(len(service_index()) == 63, f"63 modules in service, not {len(service_index())}")
    check(len(registry_index()) == 101, f"101 in the registry, not {len(registry_index())}")
    check(sorted(CORE_VOTING_MODULES) == ["A1.7", "A1.8"],
          "the voting count is exactly 2, A1.7 and A1.8", str(sorted(CORE_VOTING_MODULES)))

    print()
    print("=" * 78)
    print("10. RUN 75: A ROW EXISTING IS NOT THE SAME AS A RESULT EXISTING")
    print("=" * 78)
    # APPENDED, NEVER INSERTED. Section 10 is new and sections 1-9 above are untouched, so the
    # positional ladder this file is is extended rather than rewritten.
    #
    # WHAT THIS ADDS TO RUN 48'S RULING. Run 48 established WHERE the list comes from -- the
    # result table, never the document table and never a generated range -- and every check
    # above still asserts that. Run 75 establishes WHAT COUNTS AS BEING ON IT. The owner's
    # project carried a complete period 1 and a live period 2 holding no status and no module
    # results, and the page opened on period 2 and drew nothing. Compute no longer writes such a
    # row, and this section pins the OTHER half: a row inserted by any path that is not compute
    # must not be selected either.
    from app.research_models import ComputedResult as _CR, new_ulid as _ulid  # noqa: E402

    _before = periods_view(FOUR)
    check(_before["latest_computed_period"] == 4 and _before["computed_periods"] == [1, 2, 3, 4],
          "PRJ-R48-FOUR opens on 4 before an empty row is planted", str(_before))

    with Session() as _s:
        _proj = _s.scalar(select(Project).where(Project.legacy_id == FOUR))
        _live4 = _s.scalar(select(_CR).where(_CR.project_id == _proj.id, _CR.period == 4,
                                             _CR.superseded_by.is_(None)))
        _s.add(_CR(result_id=_ulid(), project_id=_proj.id, period=9,
                   signal_inputs={}, module_results=[], category_statuses={},
                   project_status=None, portfolio_snapshot=None,
                   simulation_version=_live4.simulation_version, seed=_live4.seed,
                   period_cutoff=_live4.period_cutoff, source_documents=[], abstained=None))
        _s.commit()

    # NON-VACUITY. The row really is there and really is live: if the insert had not landed, or
    # if it were superseded, the checks below would pass for the wrong reason.
    with Session() as _s:
        _proj = _s.scalar(select(Project).where(Project.legacy_id == FOUR))
        _planted = _s.scalar(select(_CR).where(_CR.project_id == _proj.id, _CR.period == 9))
        check(_planted is not None and _planted.superseded_by is None
              and not (_planted.module_results or []),
              "the empty row for period 9 is LIVE in the table, so the checks below are not "
              "vacuous",
              f"present={_planted is not None} "
              f"live={_planted is not None and _planted.superseded_by is None} "
              f"modules={len(_planted.module_results or []) if _planted else None}")

    _after = periods_view(FOUR)
    check(_after["latest_computed_period"] == 4,
          "AND THE PAGE STILL OPENS ON 4: a live row holding no module results is not a result, "
          "so it does not become the latest computed period",
          str(_after["latest_computed_period"]))
    check(_after["computed_periods"] == [1, 2, 3, 4],
          "and period 9 is not listed as computed at all",
          str(_after["computed_periods"]))

    # AND THE COMPUTE HALF: a period holding no document produces nothing, not an empty row.
    _c9 = post({"action": "projectcompute", "session_token": pm, "id": TWO, "period": 7})
    check(_c9.get("ok") is False and "no documents" in str(_c9.get("error", "")),
          "compute over a period holding no documents is REFUSED, so no empty row is written",
          str(_c9)[:200])
    with Session() as _s:
        _proj = _s.scalar(select(Project).where(Project.legacy_id == TWO))
        _n7 = _s.scalar(select(func.count()).select_from(_CR)
                        .where(_CR.project_id == _proj.id, _CR.period == 7))
        check(_n7 == 0, "and no row of any kind exists for that period afterwards", str(_n7))

except BaseException as _exc:                                  # noqa: BLE001
    # A CRASH IS NOT A PASS. Without this arm the `finally` below called sys.exit and swallowed
    # the traceback, so a section that raised printed a clean RESULT line one check short.
    import traceback
    FAILED += 1
    print()
    print("  ****  THE SUITE RAISED, which is a failure and not a skipped section:")
    traceback.print_exc()
finally:
    print()
    print(f"RESULT: {PASSED}/{PASSED + FAILED} checks passed")
    sys.exit(1 if FAILED else 0)
