"""
Facade storage model. JSONB first.

The whole project.json is stored in projects.doc rather than shredded into columns. The Apps
Script backend has no fixed project schema: the captured fixtures show `list` rows carrying
geocode fields that `listarchived` rows do not, and every project carries a different set of
signalInputs keys. Shredding would force a column set the source data does not have, and any
key the migration did not anticipate would be silently dropped, which is the one failure a
compatibility facade must not have.

Types use dialect variants so the same models and the same migration run on Postgres (JSONB,
native UUID) and on SQLite for local verification.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from .db import Base

# JSONB on Postgres, JSON on SQLite.
JSONType = JSONB().with_variant(JSON(), "sqlite")
# SQLAlchemy's dialect-agnostic Uuid: native uuid on Postgres, CHAR(32) elsewhere. A
# postgresql.UUID().with_variant(String) was tried first and fails on SQLite, which cannot bind a
# Python UUID object because the variant swaps the DDL type but not the bind processor.
UUIDType = Uuid(as_uuid=True)


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=_uuid)

    # The display id the frontend uses everywhere, for example "PRJ-08421". Unique, and the only
    # identifier that appears in /exec requests.
    legacy_id: Mapped[str] = mapped_column(Text, nullable=False, unique=True, index=True)

    doc: Mapped[dict] = mapped_column(JSONType, nullable=False)

    # Optimistic concurrency. Writes in A1b compare and increment; nothing increments it yet.
    record_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    archived: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false", index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    snapshots: Mapped[list["ProjectSnapshot"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    files: Mapped[list["File"]] = relationship(back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("legacy_id", name="uq_projects_legacy_id"),)


class ProjectSnapshot(Base):
    """
    Backs ?action=gethistory.

    Deliberately separate from projects.doc["history"]. The capture proves these are different
    stores: PRJ-08421 carries four entries in doc["history"] while gethistory returns []. Reading
    history out of the document would have produced four rows where the live backend returns none.
    """

    __tablename__ = "project_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    period: Mapped[str] = mapped_column(Text, nullable=True)
    snapshot: Mapped[dict] = mapped_column(JSONType, nullable=False)
    saved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="snapshots")


class File(Base):
    """
    Backs ?action=listcorpus and ?action=listauditresults, distinguished by doc_type.

    Note that this table does NOT drive the slim docCount. The capture shows docCount equals the
    number of signals_extracted events in the project document, not the number of corpus files:
    PRJ-08421 reports docCount 36 while listcorpus returns 3 entries.
    """

    __tablename__ = "files"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    drive_file_id: Mapped[str] = mapped_column(Text, nullable=True, index=True)
    name: Mapped[str] = mapped_column(Text, nullable=True)
    doc_type: Mapped[str] = mapped_column(Text, nullable=True, index=True)
    sha256: Mapped[str] = mapped_column(String(64), nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    project: Mapped[Project] = relationship(back_populates="files")
