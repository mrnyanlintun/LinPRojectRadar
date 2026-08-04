"""projects.is_training: the single source of truth training isolation is built on

Revision ID: 0018_project_training
Revises: 0017_participant_theme
Create Date: 2026-08-04

ONE COLUMN, ON `projects`, AND NOTHING SETS IT TRUE YET.

Training mode (run 1) builds the flag that turns the feature on and the refusal that keeps a
research account off it. It does not generate a training project — that is a later run. This
column exists now anyway, because it is the part of training mode that cannot be retrofitted:
once study data collection starts, a practice decision that reached the analytical record is
indistinguishable from a real one, and no later migration reaches back to unmix it. The column
and the read-path filters that key off it (`research_export.build_module_results_rows`,
documented in the run's report) are built now, ahead of anything that could populate it, so the
first training project a later run creates is already excluded by construction rather than by
someone remembering to add a filter once the risk is live.

NOT NULL, DEFAULT FALSE. Every project that exists before this migration runs resolves to "not
training" — the only correct reading for a project nothing has ever marked otherwise — and
every project created between this deploy and the run that actually builds training-project
generation keeps resolving the same way, because there is no code path yet that could pass
anything else.

INDEXED. The isolation filters are unconditional WHERE clauses on this column over the whole
`projects` table (the project_health export scope has no other project-level filter to piggy-
back an index on), so it is indexed the same way `archived` already is.

WHY NOT A COLUMN PER TABLE THAT MIGHT CARRY TRAINING DATA INSTEAD

`decisions`, `computed_results` and the state store a later run adds all reference a project.
Marking training on the project and having every dependent read join back to it means there is
exactly one place a row can be training and exactly one place to check — the alternative,
copying a training flag onto every table that touches a training project, is the kind of
duplicated source of truth that drifts the first time one write path forgets to set it.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


revision = "0018_project_training"
down_revision = "0017_participant_theme"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column("is_training", sa.Boolean(), nullable=False,
                  server_default=sa.text("false")),
    )
    op.create_index("ix_projects_is_training", "projects", ["is_training"])


def downgrade() -> None:
    op.drop_index("ix_projects_is_training", table_name="projects")
    op.drop_column("projects", "is_training")
