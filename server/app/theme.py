"""
The interface theme: an operational preference, and a fixed value for research.

WHY THIS IS ENFORCED ON THE SERVER RATHER THAN BY HIDING A CONTROL

Every research participant must see identical stimulus. The four themes do not merely recolour
the page: on the plain theme a status is a dark saturated mark on white and on the dark themes
it is a bright mark on near-black, and how prominent a Red reads is exactly the kind of thing
that could move a decision. A participant who changed theme would be a participant running a
different experiment, and nobody would know from the export which one they had run.

So the theme is refused for research accounts the same way project creation is: in
`gate_action`, before dispatch, audited, with a plain reason. Hiding the fly-out would be a
suggestion. `a_themeget` additionally IGNORES any stored value for a research account, so even
a row written before this existed, or written by an administrator, or left behind when an
account changed type, renders the fixed theme.

THE FIXED THEME IS THE EXISTING DEFAULT, NOT THE NEW ONE. Research participants have been
seeing `newyork` throughout, and the study's stimulus should not change because a theme was
added for operational users. That is also the reason the default for an operational account
who has never chosen is `newyork`: nobody's appearance changes until they choose.
"""

from __future__ import annotations

from typing import Any, Callable

import sqlalchemy as sa
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from .facade import err
from .research_identity import audit, resolve_caller

# The closed vocabulary, matching OFFERED_THEMES in assets/js/app.js. `dark` (Gotham) is
# archived there and is deliberately absent here: it still renders if forced, but it is not a
# value a caller may store.
THEMES: tuple[str, ...] = ("plain", "light", "newyork", "maria")

# What an account sees when it has not chosen, and what a research account sees always.
DEFAULT_THEME: str = "newyork"
RESEARCH_THEME: str = DEFAULT_THEME

__all__ = [
    "THEMES", "DEFAULT_THEME", "RESEARCH_THEME",
    "resolve_theme", "stored_theme", "THEME_ACTIONS",
]


def stored_theme(session: Session, participant_id: str) -> str | None:
    """
    The raw column value, or None. Read by hand for the same reason features are.

    NEVER RAISES, EVEN IF THE COLUMN DOES NOT EXIST YET. 2026-08-02: code that expects
    `participants.theme` deployed before the migration that adds it was applied (migrations are
    applied by hand, deliberately, after the deploy), and every sign-in raised ProgrammingError
    for the whole gap. The ORM mapping that caused that is gone (see research_models.py), but this
    is the second line of defence for the same class of failure: a database mid-migration, or a
    rollback that drops the column back out, must degrade this ONE preference to "not chosen"
    rather than take anything down. `resolve_theme` already treats None as "use the default", so
    this failure mode was always survivable here; it just was not caught before it could matter.

    Rolls back on failure. A raised DBAPIError leaves the session's transaction unusable for
    anything after it until it is rolled back, and this must not be the reason a caller's next
    query fails too.
    """
    try:
        raw = session.execute(
            sa.text("SELECT theme FROM participants WHERE participant_id = :pid"),
            {"pid": participant_id},
        ).scalar()
    except DBAPIError:
        session.rollback()
        return None
    value = (raw or "").strip()
    return value or None


def resolve_theme(session: Session, participant) -> str:
    """
    The theme this account renders. Never raises, never returns an unknown value.

    A research account resolves to RESEARCH_THEME whatever is stored. An unrecognised string
    resolves to the default rather than raising: a theme retired from the vocabulary should
    make old rows fall back, not make an account fail to load.
    """
    if getattr(participant, "account_type", None) == "research":
        return RESEARCH_THEME
    value = stored_theme(session, participant.participant_id)
    return value if value in THEMES else DEFAULT_THEME


def _write_theme(session: Session, participant_id: str, theme: str) -> None:
    session.execute(
        sa.text("UPDATE participants SET theme = :t WHERE participant_id = :pid"),
        {"t": theme, "pid": participant_id},
    )


# ---------------------------------------------------------------- actions


def a_themeget(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    The theme to render, and whether this caller may change it.

    `fixed` is what the interface keys off to decide whether to offer the control. It is a
    convenience for the interface and NOT the enforcement: `themeset` refuses independently,
    so a caller who ignores this field and posts anyway is still refused.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    participant = caller.participant
    is_research = participant.account_type == "research"
    return {
        "ok": True,
        "theme": resolve_theme(session, participant),
        "default_theme": DEFAULT_THEME,
        "themes": list(THEMES),
        "fixed": is_research,
        "account_type": participant.account_type,
        # Stated so an administrator reading a response can tell "has not chosen" from
        # "chose the default", and so a research account's ignored row is visible rather
        # than silently dropped.
        "stored": stored_theme(session, participant.participant_id),
    }


def a_themeset(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Record an operational account's chosen theme.

    The research refusal lives in `gate_action` (features.py), before dispatch, so this
    handler is not the only thing standing between a participant and a theme change. The
    check is repeated here anyway: a handler that assumes an upstream gate is a handler that
    breaks silently the day the gate is refactored.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    participant = caller.participant

    if participant.account_type == "research":
        audit(session, "theme_change_denied", participant_id=caller.participant_id,
              account_type=participant.account_type,
              requested=str(payload.get("theme") or "")[:40])
        session.commit()
        return err("not available: the interface theme is fixed for this account so that "
                   "every participant sees the same thing.")

    requested = str(payload.get("theme") or "").strip()
    if requested not in THEMES:
        return err(f"unknown theme: {requested or '(empty)'}; "
                   f"recognized themes are {', '.join(THEMES)}")

    # Writing has no fallback the way reading does — there is nowhere else to put the choice — so
    # this cannot degrade silently. It CAN avoid being an unhandled 500: if the column is not
    # there yet (schema behind the code, the same gap that caused the 2026-08-02 outage), refuse
    # with a plain reason instead of letting a DBAPIError surface as "Server error: ...".
    try:
        _write_theme(session, caller.participant_id, requested)
    except DBAPIError:
        session.rollback()
        return err("the theme preference cannot be saved right now; try again shortly.")
    audit(session, "theme_set", participant_id=caller.participant_id, theme=requested)
    session.commit()
    return {"ok": True, "theme": requested, "themes": list(THEMES), "fixed": False}


THEME_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "themeget": a_themeget,
    "themeset": a_themeset,
}
