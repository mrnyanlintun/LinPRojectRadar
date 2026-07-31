#!/usr/bin/env python3
"""
Seed the facade database from the M0 captured fixtures.

This exists so the facade can be verified against the live contract with the same data the live
backend returned. It is a verification aid, not a migration path: real data movement is A1b.

Seeded from p0-baseline/contracts/get/:
    list.json            -> projects (archived = false)
    listarchived.json    -> projects (archived = true)
    listcorpus.json      -> files for the captured project
    listauditresults.json-> files with doc_type "audit_result"
    gethistory.json      -> project_snapshots (empty for the captured project, which is the point:
                            doc["history"] has four entries while gethistory returns none)

Usage:
    DATABASE_URL=... python tools/seed_from_fixtures.py --project-id PRJ-08421
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from sqlalchemy import delete, select  # noqa: E402

from app.db import build_engine, build_session_factory  # noqa: E402
from app.models import File, Project, ProjectSnapshot  # noqa: E402
from app.settings import load_settings  # noqa: E402

FIXTURES = pathlib.Path(__file__).resolve().parents[2] / "p0-baseline" / "contracts" / "get"


def load(name: str) -> dict:
    return json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8"))


def parse_ts(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-id", default="PRJ-08421",
                        help="Project the per-project fixtures were captured against.")
    args = parser.parse_args()

    engine = build_engine(load_settings())
    Session = build_session_factory(engine)

    with Session() as session:
        # Idempotent: a re-run reproduces the same state rather than duplicating rows.
        session.execute(delete(File))
        session.execute(delete(ProjectSnapshot))
        session.execute(delete(Project))
        session.commit()

        created = 0
        # created_at is assigned in fixture order so that _ordered() reproduces the live ordering,
        # which the captured list and listslim fixtures share.
        base = datetime(2020, 1, 1, tzinfo=timezone.utc)
        for archived, fixture in ((False, "list"), (True, "listarchived")):
            for i, doc in enumerate(load(fixture)["projects"]):
                session.add(Project(
                    legacy_id=doc["id"],
                    doc=doc,
                    archived=archived,
                    created_at=base.replace(microsecond=created + 1) if False else base,
                    updated_at=parse_ts(doc.get("updatedAt")),
                ))
                created += 1
        session.commit()

        # Re-stamp created_at in fixture order. Done as a second pass because server_default
        # would otherwise give every row the same transaction timestamp and lose the ordering.
        order = [d["id"] for d in load("list")["projects"]] + \
                [d["id"] for d in load("listarchived")["projects"]]
        for i, legacy in enumerate(order):
            p = session.scalar(select(Project).where(Project.legacy_id == legacy))
            if p:
                p.created_at = datetime(2020, 1, 1, 0, 0, i, tzinfo=timezone.utc)
        session.commit()

        target = session.scalar(select(Project).where(Project.legacy_id == args.project_id))
        if target is None:
            print(f"Project {args.project_id} not among the seeded projects; per-project fixtures skipped.")
            return 1

        corpus = load("listcorpus").get("corpus") or []
        for entry in corpus:
            session.add(File(
                project_id=target.id,
                drive_file_id=entry.get("fileId"),
                name=entry.get("name"),
                doc_type=entry.get("docType"),
                ingested_at=parse_ts(entry.get("ingestedAt")),
            ))

        results = load("listauditresults").get("results") or []
        for entry in results:
            session.add(File(
                project_id=target.id,
                drive_file_id=entry.get("fileId"),
                name=entry.get("name"),
                doc_type="audit_result",
                ingested_at=parse_ts(entry.get("createdAt")),
            ))

        for entry in load("gethistory").get("history") or []:
            session.add(ProjectSnapshot(project_id=target.id, period=None, snapshot=entry))

        session.commit()

        print(f"seeded projects={created} corpus={len(corpus)} audit_results={len(results)} "
              f"snapshots={len(load('gethistory').get('history') or [])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
