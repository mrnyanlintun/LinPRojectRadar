"""participants.theme: the interface theme an operational account has chosen

Revision ID: 0017_participant_theme
Revises: 0016_document_filing
Create Date: 2026-08-02

ONE NULLABLE COLUMN, AND NULL IS THE ANSWER FOR ALMOST EVERY ROW.

NULL means "has not chosen", which resolves to the default theme. That is deliberate: the
requirement is that an existing user's appearance does not change until they choose, and a
nullable column with no server default is the only shape where that is true by construction
rather than by remembering to write the old value into every existing row.

WHY THIS IS NOT A KEY IN `participants.features`

`features` is a JSONB map of BOOLEAN flags, resolved by `effective_features` against a
per-account-type default, and every consumer of it assumes `bool`. A theme is a short string
from a closed vocabulary with a different default rule, so putting it there would mean either
teaching that resolver about a non-boolean value or storing a set of mutually exclusive
booleans, one per theme, which is a vocabulary that cannot be validated. A column says what it
is.

WHY THE COLUMN IS NOT CONSTRAINED TO THE THEME LIST

The vocabulary lives in `app/theme.py` (THEMES) and is validated on write. A CHECK constraint
here would pin the list in the schema as well, so adding or retiring a theme would need a
migration to accompany a CSS change, and a value retired in code would make existing rows
invalid rather than simply unrecognised. `resolve_theme` treats anything it does not recognise
as "not chosen" and returns the default, so an unknown string degrades to the safe answer
instead of raising.

RESEARCH ACCOUNTS MAY HOLD A VALUE AND IT IS IGNORED. The column is not gated at the schema
level, because the gate belongs where it can be audited and explained: a research participant's
theme is fixed regardless of what this column says, and `a_themeset` refuses to write it for
them at all. Storing nothing for them would look identical to storing something and ignoring
it, right up until an account changes type, and then the ignored value would silently become
live. Ignoring it on read is the behaviour that survives that.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0017_participant_theme"
down_revision = "0016_document_filing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("participants", sa.Column("theme", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("participants", "theme")
