#!/usr/bin/env python3
"""
Run 93, goal two: DOES A DIFFERENT MODEL READ THE SAME SPECIFICATION THE SAME WAY?

THIS TOOL WAS NOT RUN IN THE RUN 93 VERIFICATION SESSION. There was no provider key of any kind
in that environment, so goal two was unreachable there and NOTHING was simulated in its place.
This is the exact command that answers it on a deployment that HAS keys.

It takes the SAME stored rows -- one project, one period, the `signal_inputs` already stored on
the live computed_results row -- and applies the SAME eleven specifications under TWO provider
settings, back to back, in one process. Nothing is re-extracted and nothing is recomputed; only
the model that reads the specification differs. It writes NOTHING to the database: it is a
measurement, not a press.

  REFUSES to run unless BOTH providers' keys are present. It never substitutes a recorded
  fixture for a missing key, and it never reports one provider's answer as the other's.

USAGE (from server/), with a DEV CLONE of the database, never production Postgres:

    DATABASE_URL=... \\
    ANTHROPIC_API_KEY=... GROQ_API_KEY=... \\
    PYTHONIOENCODING=utf-8 python tools/run93_provider_comparison.py \\
        --project <PROJECT_ID> --period <N> --a anthropic --b groq

Per category and per module it reports whether the two readings MATCHED on: the module's state,
its disposition (the band), and its value. Where they differ it says how -- a different number,
a different band, a different abstention reason, or a malformed response that could not be read
at all.
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from app import ai_provider as ap
from app.db import build_engine, build_session_factory
from app.models import Project
from app.research_models import ComputedResult
from app.settings import load_settings
from app.simulation import spec_apply as sa


def applier_for(provider: str):
    """The named provider or a loud refusal. NEVER a recorded fixture, never another provider."""
    env = dict(os.environ)
    env["AI_SPEC_PROVIDER"] = provider
    cfg = ap.load_provider("spec", env)
    if not cfg.key_present(env):
        raise SystemExit(
            f"REFUSING TO RUN: provider {provider!r} has no key ({cfg.key_env} is not set in "
            f"this environment). This comparison is only meaningful when both sides are real "
            f"model calls. Nothing is simulated in its place.")
    return sa.ProviderSpecApplier(
        ap.build_client(cfg, timeout_s=sa.REQUEST_TIMEOUT_S, environ=env))


def modules_of(row: dict) -> dict[str, dict]:
    return {m.get("module_id"): m for m in (row.get("modules") or []) if m.get("module_id")}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--project", required=True)
    p.add_argument("--period", type=int, required=True)
    p.add_argument("--a", default="anthropic")
    p.add_argument("--b", default="groq")
    args = p.parse_args()

    a_applier, b_applier = applier_for(args.a), applier_for(args.b)
    print(f"A = {a_applier.provider}/{a_applier.model_id}")
    print(f"B = {b_applier.provider}/{b_applier.model_id}")
    print("Both sides are REAL MODEL CALLS. Neither side is a fixture.\n")

    Session = build_session_factory(build_engine(load_settings()))
    with Session() as session:
        project = session.query(Project).filter(
            Project.legacy_id == args.project).one_or_none()
        if project is None:
            raise SystemExit(f"no project {args.project!r}")
        result = session.query(ComputedResult).filter(
            ComputedResult.project_id == project.id,
            ComputedResult.period == args.period,
            ComputedResult.superseded_by.is_(None)).one_or_none()
        if result is None:
            raise SystemExit(f"no live computed result for period {args.period}")
        figures = result.signal_inputs or {}

    keys = [k for k in sa.ALL_CATEGORIES if sa.has_specification(k)]
    same_count = diff_count = 0
    for key in keys:
        ra = sa.apply_category(key, figures, a_applier)
        rb = sa.apply_category(key, figures, b_applier)
        cat_same = (ra["state"] == rb["state"] and ra["status"] == rb["status"])
        print(f"{key}: A state={ra['state']} status={ra['status']} | "
              f"B state={rb['state']} status={rb['status']} -> "
              f"{'MATCH' if cat_same else 'DIFFER'}")
        if ra["state"] == "failed" or rb["state"] == "failed":
            print(f"   A reason: {ra.get('reason')}")
            print(f"   B reason: {rb.get('reason')}")
        ma, mb = modules_of(ra), modules_of(rb)
        for mid in sorted(set(ma) | set(mb)):
            x, y = ma.get(mid), mb.get(mid)
            if x is None or y is None:
                print(f"   {mid}: PRESENT ONLY IN {'A' if y is None else 'B'}")
                diff_count += 1
                continue
            how = []
            if x.get("state") != y.get("state"):
                how.append(f"state {x.get('state')} vs {y.get('state')}")
            if x.get("band") != y.get("band"):
                how.append(f"band {x.get('band')} vs {y.get('band')}")
            if x.get("value") != y.get("value"):
                how.append(f"value {x.get('value')} vs {y.get('value')}")
            if x.get("state") == y.get("state") == "abstained" and \
                    x.get("reason") != y.get("reason"):
                how.append("different abstention reason")
            if how:
                diff_count += 1
                print(f"   {mid}: DIFFER -- " + "; ".join(how))
            else:
                same_count += 1
    print(f"\nmodules matched: {same_count}   modules differing: {diff_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
