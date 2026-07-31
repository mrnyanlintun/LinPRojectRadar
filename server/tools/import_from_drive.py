#!/usr/bin/env python3
"""
One-way import: Google Drive to Postgres, plus the reconciliation report.

The import is the mechanism. The reconciliation is the deliverable: an import that "worked" but
moved 11 of 12 projects is worse than one that failed, because nothing announces the missing one.
So this script always ends by comparing both stores and writing a report, and it exits non-zero if
any discrepancy is unexplained.

Read-only against Drive. Nothing here writes to Drive, and the adapter has no write path. Apps
Script remains the authoritative writer until M7.

Dry run by default. --apply is required to write anything to Postgres.

Usage:
    DATABASE_URL=... GOOGLE_SERVICE_ACCOUNT_JSON=... python tools/import_from_drive.py
    DATABASE_URL=... GOOGLE_SERVICE_ACCOUNT_JSON=... python tools/import_from_drive.py --apply
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import datetime, timezone

sys.path.insert(0, __file__.rsplit("tools", 1)[0])

from sqlalchemy import func, select  # noqa: E402

from app.db import build_engine, build_session_factory  # noqa: E402
from app.drive_adapter import (  # noqa: E402
    CREDENTIAL_ENV, DriveError, DriveProject, build_service, enumerate_projects,
    parent_folder_id, period_from_filename,
)
from app.models import File, Project, ProjectSnapshot  # noqa: E402
from app.settings import load_settings  # noqa: E402

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
REPORT_ROOT = REPO_ROOT / "p0-baseline" / "reconciliation"

# doc_type recorded per source folder. listcorpus excludes audit_result, so the labels matter.
DOC_TYPE_BY_FOLDER = {
    "_corpus": "corpus",
    "_audits": "audit_result",
    "_signals": "signal",
    "_history": "history",
}


def upsert_projects(session, drive_projects: list[DriveProject]) -> dict[str, int]:
    """
    Idempotent by legacy_id.

    An existing row is updated in place rather than deleted and recreated, so its primary key,
    created_at and any research reference to it survive a re-run.
    """
    counts = {"inserted": 0, "updated": 0, "skipped_unparseable": 0}

    for dp in drive_projects:
        if dp.doc is None:
            counts["skipped_unparseable"] += 1
            continue

        row = session.scalar(select(Project).where(Project.legacy_id == dp.legacy_id))
        if row is None:
            session.add(Project(legacy_id=dp.legacy_id, doc=dp.doc, archived=dp.archived))
            counts["inserted"] += 1
        else:
            row.doc = dp.doc            # replaced, never mutated: JSON change tracking
            row.archived = dp.archived
            counts["updated"] += 1

    session.flush()
    return counts


def upsert_history(session, drive_projects: list[DriveProject], service) -> dict[str, int]:
    """
    History snapshots, keyed by (project, period).

    The period comes from the filename. A file whose name yields no period is counted and named in
    the report rather than stored under a made-up period.
    """
    counts = {"inserted": 0, "updated": 0, "no_period": 0, "unreadable": 0}

    for dp in drive_projects:
        if dp.doc is None:
            continue
        project = session.scalar(select(Project).where(Project.legacy_id == dp.legacy_id))
        if project is None:
            continue

        for f in dp.history:
            period = period_from_filename(f.name)
            if period is None:
                counts["no_period"] += 1
                continue

            from app.drive_adapter import read_json_file  # noqa: PLC0415
            doc, problem = read_json_file(service, f.file_id)
            if problem or doc is None:
                counts["unreadable"] += 1
                continue

            existing = session.scalar(
                select(ProjectSnapshot).where(ProjectSnapshot.project_id == project.id,
                                              ProjectSnapshot.period == period)
            )
            if existing is None:
                session.add(ProjectSnapshot(project_id=project.id, period=period, snapshot=doc))
                counts["inserted"] += 1
            else:
                existing.snapshot = doc
                counts["updated"] += 1

    session.flush()
    return counts


def upsert_files(session, drive_projects: list[DriveProject]) -> dict[str, int]:
    """
    File metadata only. No bytes are downloaded in this phase, so sha256 is left null unless Drive
    supplies its own checksum, which is md5 and is recorded as such rather than passed off as a
    sha256.
    """
    counts = {"inserted": 0, "updated": 0}

    for dp in drive_projects:
        if dp.doc is None:
            continue
        project = session.scalar(select(Project).where(Project.legacy_id == dp.legacy_id))
        if project is None:
            continue

        for f in dp.all_files:
            if f.parent_folder == "_history":
                continue  # history lands in project_snapshots, not files
            doc_type = DOC_TYPE_BY_FOLDER.get(f.parent_folder or "", "unknown")

            existing = session.scalar(select(File).where(File.drive_file_id == f.file_id))
            if existing is None:
                session.add(File(project_id=project.id, drive_file_id=f.file_id, name=f.name,
                                 doc_type=doc_type, sha256=None))
                counts["inserted"] += 1
            else:
                existing.project_id = project.id
                existing.name = f.name
                existing.doc_type = doc_type
                counts["updated"] += 1

    session.flush()
    return counts


def reconcile(session, drive_projects: list[DriveProject]) -> dict:
    """Compare both stores and describe every difference."""
    drive_by_id = {dp.legacy_id: dp for dp in drive_projects}
    db_rows = session.scalars(select(Project)).all()
    db_by_id = {row.legacy_id: row for row in db_rows}

    report: dict = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "parent_folder_id": parent_folder_id(),
        "counts": {
            "drive_project_folders": len(drive_projects),
            "postgres_projects": len(db_rows),
            "drive_parseable": sum(1 for d in drive_projects if d.doc is not None),
            "drive_unparseable": sum(1 for d in drive_projects if d.doc is None),
        },
        "per_project": [],
        "discrepancies": [],
        "explained": [],
    }

    def flag(kind: str, detail: str, **extra) -> None:
        report["discrepancies"].append({"kind": kind, "detail": detail, **extra})

    for dp in drive_projects:
        if dp.doc is None:
            # Named, not silently dropped, and explained rather than counted as a mismatch: a
            # folder we could not parse is a known state, not an unknown one.
            report["explained"].append({
                "kind": "unparseable_project_json",
                "legacy_id": dp.legacy_id,
                "detail": dp.parse_error or "unknown parse failure",
            })

    for legacy_id in sorted(set(drive_by_id) | set(db_by_id)):
        dp = drive_by_id.get(legacy_id)
        row = db_by_id.get(legacy_id)

        if dp is None:
            flag("in_postgres_not_in_drive",
                 f"project {legacy_id} exists in Postgres but not under the Drive parent",
                 legacy_id=legacy_id)
            continue
        if row is None:
            if dp.doc is None:
                report["explained"].append({
                    "kind": "not_imported_unparseable",
                    "legacy_id": legacy_id,
                    "detail": "project.json could not be parsed, so the project was not imported",
                })
            else:
                flag("in_drive_not_in_postgres",
                     f"project {legacy_id} exists in Drive but was not imported",
                     legacy_id=legacy_id)
            continue

        db_history = session.scalar(select(func.count()).select_from(ProjectSnapshot)
                                    .where(ProjectSnapshot.project_id == row.id)) or 0
        db_corpus = session.scalar(select(func.count()).select_from(File)
                                   .where(File.project_id == row.id,
                                          File.doc_type == "corpus")) or 0
        db_audits = session.scalar(select(func.count()).select_from(File)
                                   .where(File.project_id == row.id,
                                          File.doc_type == "audit_result")) or 0

        drive_history_with_period = [f for f in dp.history if period_from_filename(f.name)]

        entry = {
            "legacy_id": legacy_id,
            "archived": bool(row.archived),
            "drive_history_files": len(dp.history),
            "drive_history_with_period": len(drive_history_with_period),
            "postgres_history_snapshots": db_history,
            "drive_corpus_files": len(dp.corpus),
            "postgres_corpus_files": db_corpus,
            "drive_audit_files": len(dp.audits),
            "postgres_audit_files": db_audits,
            "drive_signal_files": len(dp.signals),
        }
        report["per_project"].append(entry)

        if len(drive_history_with_period) != db_history:
            flag("history_count_mismatch",
                 f"{legacy_id}: Drive has {len(drive_history_with_period)} datable history files, "
                 f"Postgres has {db_history} snapshots", legacy_id=legacy_id)
        if len(dp.history) != len(drive_history_with_period):
            report["explained"].append({
                "kind": "history_file_without_period",
                "legacy_id": legacy_id,
                "detail": (f"{len(dp.history) - len(drive_history_with_period)} history file(s) "
                           f"have no recognisable period in the filename and were not imported"),
            })
        if len(dp.corpus) != db_corpus:
            flag("corpus_count_mismatch",
                 f"{legacy_id}: Drive has {len(dp.corpus)} corpus files, Postgres has {db_corpus}",
                 legacy_id=legacy_id)
        if len(dp.audits) != db_audits:
            flag("audit_count_mismatch",
                 f"{legacy_id}: Drive has {len(dp.audits)} audit files, Postgres has {db_audits}",
                 legacy_id=legacy_id)

    # Orphans: a files row whose drive_file_id no longer exists in Drive.
    drive_file_ids = {f.file_id for dp in drive_projects for f in dp.all_files}
    for row in session.scalars(select(File)).all():
        if row.drive_file_id and row.drive_file_id not in drive_file_ids:
            flag("orphaned_drive_file_id",
                 f"files row {row.name!r} references Drive id {row.drive_file_id} which is not "
                 f"present under the parent folder", drive_file_id=row.drive_file_id)

    report["counts"]["discrepancies"] = len(report["discrepancies"])
    report["counts"]["explained"] = len(report["explained"])
    report["clean"] = not report["discrepancies"]
    return report


def render_markdown(report: dict, applied: bool) -> str:
    lines = [
        "# Drive to Postgres reconciliation",
        "",
        f"Generated: {report['generated_at_utc']}",
        f"Parent folder: `{report['parent_folder_id']}`",
        f"Mode: {'APPLIED' if applied else 'DRY RUN (no writes)'}",
        "",
        "## Counts",
        "",
        "| Measure | Value |",
        "|---|---|",
    ]
    for key, value in report["counts"].items():
        lines.append(f"| {key.replace('_', ' ')} | {value} |")

    lines += ["", "## Per project", "",
              "| project | archived | hist files | datable | pg snapshots | corpus | pg corpus | "
              "audits | pg audits | signals |", "|---|---|---|---|---|---|---|---|---|---|"]
    for e in report["per_project"]:
        lines.append(
            f"| {e['legacy_id']} | {e['archived']} | {e['drive_history_files']} | "
            f"{e['drive_history_with_period']} | {e['postgres_history_snapshots']} | "
            f"{e['drive_corpus_files']} | {e['postgres_corpus_files']} | "
            f"{e['drive_audit_files']} | {e['postgres_audit_files']} | {e['drive_signal_files']} |"
        )

    lines += ["", "## Discrepancies", ""]
    if report["discrepancies"]:
        for d in report["discrepancies"]:
            lines.append(f"- **{d['kind']}**: {d['detail']}")
    else:
        lines.append("None. Every project, history period, corpus item and audit result is "
                     "accounted for, and no orphaned Drive file ids were found.")

    lines += ["", "## Explained differences", ""]
    if report["explained"]:
        lines.append("These are differences with a known cause. They are listed so the count "
                     "difference is never silent.")
        lines.append("")
        for e in report["explained"]:
            lines.append(f"- **{e['kind']}** ({e.get('legacy_id', 'n/a')}): {e['detail']}")
    else:
        lines.append("None.")

    lines += ["", "## Verdict", "",
              ("PASS: no unexplained discrepancies." if report["clean"]
               else "FAIL: unexplained discrepancies above must be resolved before this import "
                    "is considered successful."), ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Import Drive project data into Postgres.")
    parser.add_argument("--apply", action="store_true",
                        help="Write to Postgres. Without it the script reads and reports only.")
    parser.add_argument("--parent", default=None, help="Override the Drive parent folder id.")
    args = parser.parse_args()

    try:
        service = build_service()
    except DriveError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    parent = args.parent or parent_folder_id()
    print(f"Reading Drive parent folder {parent} (read-only)...")
    drive_projects = enumerate_projects(service, parent)
    print(f"  found {len(drive_projects)} project folder(s)")
    for dp in drive_projects:
        if dp.doc is None:
            print(f"  ! {dp.legacy_id}: {dp.parse_error}")

    engine = build_engine(load_settings())
    Session = build_session_factory(engine)

    with Session() as session:
        if args.apply:
            print("Applying to Postgres...")
            p = upsert_projects(session, drive_projects)
            h = upsert_history(session, drive_projects, service)
            f = upsert_files(session, drive_projects)
            session.commit()
            print(f"  projects  inserted={p['inserted']} updated={p['updated']} "
                  f"skipped={p['skipped_unparseable']}")
            print(f"  history   inserted={h['inserted']} updated={h['updated']} "
                  f"no_period={h['no_period']} unreadable={h['unreadable']}")
            print(f"  files     inserted={f['inserted']} updated={f['updated']}")
        else:
            print("DRY RUN: nothing written. Re-run with --apply to write.")

        report = reconcile(session, drive_projects)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = REPORT_ROOT / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "report.md").write_text(render_markdown(report, args.apply), encoding="utf-8")
    (out_dir / "report.json").write_text(json.dumps(report, indent=2, default=str) + "\n",
                                         encoding="utf-8")

    print()
    print(f"Reconciliation written to {out_dir}")
    print(f"  discrepancies: {report['counts']['discrepancies']}   "
          f"explained: {report['counts']['explained']}")
    print("  VERDICT:", "PASS" if report["clean"] else "FAIL")

    # Non-zero on an unexplained discrepancy, and non-zero on a dry run, so neither is mistaken
    # for a completed import by a caller that only checks the exit code.
    if not report["clean"]:
        return 1
    return 0 if args.apply else 3


if __name__ == "__main__":
    sys.exit(main())
