#!/usr/bin/env python3
"""
RUN 41 SECTION 11 - capture the AI recommendation actually delivered at every one of the 36
project-period positions, as a digest, by EXECUTING the reveal.

Run 40 established the governed binding: the recommendation is attached per ASSIGNMENT, i.e. per
project/scenario, so six projects x six periods give 36 positions carrying 6 unique project-level
exposures. Run 41 must not change it. This script is the measuring instrument for that claim: it
runs once on the pinned v25 line and once on the v26 working tree, and test_run41_preservation.py
compares the two outputs.

TWO THINGS THIS DELIBERATELY DOES NOT DO

It does not build its own study. It reuses run38_dryrun's bootstrap and participant construction,
which already stand up the governed six-project six-period design with the action families and
transition rules that make all 36 positions reachable through the participant route. A private
harness would be a second, unreviewed definition of the study.

It does not label a position from its own loop counter. An earlier version of this script did,
and reported 36 positions with one recommendation between them - because every advance had
silently refused and the participant had never left the first period, so the same idempotent
reveal was re-read 36 times and labelled with six different project names. The label is now taken
from the decisions row the application actually wrote (its assignment, hence its project, and its
own period string), and the script refuses to emit unless it observed 36 DISTINCT positions.

Usage: DATABASE_URL=... SESSION_SECRET=... python tools/run41_ai_binding_digests.py OUT.json
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, __file__.rsplit("tools", 1)[0])
sys.path.insert(0, HERE)

from sqlalchemy import select  # noqa: E402

import run38_dryrun as D  # noqa: E402
from app.research_models import Assignment, Decision  # noqa: E402

post = D.post


# THE DIGEST IS OVER RECOMMENDATION CONTENT, AND CONTENT IS DEFINED BY THE APPLICATION.
#
# A digest over the whole reveal response is useless for comparing two independent runs: the
# response carries package_id (a fresh ULID per run) and frozen_at (a wall clock), so every one
# of the 36 positions "moves" between any two runs of anything, including a run against itself.
# That is measurement noise, not a behaviour change, and reporting it as one would have falsely
# accused this run of altering the AI binding.
#
# HASHED_FIELDS is the application's own answer to "what is this recommendation's content" - the
# field list whose sha256 freezes a package and makes post-freeze edits detectable. Reusing it
# here means the comparison tracks exactly what the instrument itself treats as the recommendation
# and nothing incidental.
from app.research_decision import HASHED_FIELDS  # noqa: E402


def digest(pkgview) -> str:
    content = {f: (pkgview or {}).get(f) for f in HASHED_FIELDS}
    return hashlib.sha256(
        json.dumps(content, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


ctx = D.bootstrap()
part = D.make_participant(ctx, "R41BIND")
by_scenario = part["by_scenario"]
tok = part["token"]

positions: dict[str, dict] = {}
observed_order: list[str] = []

for _seq, aid, sid in part["assignments"]:
    for _k in range(len(D.ROUTE_PERIODS)):
        post({"action": "researchevidenceget", "session_token": tok})
        post({"action": "researchprejudgment", "session_token": tok, "pre_action": "monitor",
              "pre_confidence": 55, "pre_assessment": "r41 binding probe"})
        rev = post({"action": "researchreveal", "session_token": tok})
        assert rev.get("ok") is True, f"reveal failed: {rev}"

        # THE LABEL COMES FROM THE APPLICATION, NOT FROM THIS LOOP. Read back the decision row
        # the app just wrote and ask IT which assignment and which period this was.
        with D.SessionFactory() as s:
            rows = s.scalars(select(Decision).where(Decision.reveal_at.isnot(None))).all()
            row = max(rows, key=lambda d: (d.reveal_at, d.decision_id))
            a = s.get(Assignment, row.assignment_id)
            proj = by_scenario[a.scenario_id]
            period = row.period or "?"
        key = f"{proj}|{period}"
        if key in positions:
            raise SystemExit(
                f"position {key} was visited twice: the walk is not advancing, so these digests "
                "would be one position re-read. Refusing to emit a vacuous binding proof.")
        positions[key] = {"recommendation_digest": digest(rev.get("package")),
                          "served_package_hash": (rev.get("package") or {}).get("hash"),
                          "recommended_action": (rev.get("package") or {}).get(
                              "recommended_action"),
                          "package_hash": row.package_hash}
        observed_order.append(key)

        post({"action": "researchdecision", "session_token": tok, "final_action": "escalate",
              "disposition": "accept", "final_confidence": 70, "rationale": "r41",
              "reason_code": "cost_variance", "evidence_items": ["e1"]})
        post({"action": "researchadvance", "session_token": tok})

if len(positions) != 36:
    raise SystemExit(f"expected 36 distinct project-period positions, observed {len(positions)}; "
                     "refusing to emit an incomplete binding proof")

digs = [v["recommendation_digest"] for v in positions.values()]
per_project = {}
for k, v in positions.items():
    per_project.setdefault(k.split("|")[0], set()).add(v["recommendation_digest"])

from app.simulation.models import SIMULATION_VERSION  # noqa: E402

out = {
    "positions": positions,
    "observed_order": observed_order,
    "position_count": len(positions),
    "unique_recommendation_digests": len(set(digs)),
    "projects_with_one_recommendation_across_all_periods":
        sum(1 for v in per_project.values() if len(v) == 1),
    "simulation_version": SIMULATION_VERSION,
}
print(f"positions captured .............................. {out['position_count']}")
print(f"unique recommendation digests ................... {out['unique_recommendation_digests']}")
print(f"projects with one recommendation for all periods  "
      f"{out['projects_with_one_recommendation_across_all_periods']}/6")
print(f"simulation version .............................. {out['simulation_version']}")
json.dump(out, open(sys.argv[1], "w"), indent=2, sort_keys=True)
