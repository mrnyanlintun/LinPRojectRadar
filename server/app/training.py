"""
Training mode: the flag and the gate, run 1.

Training mode is a product feature, not part of the study: an operational user works a
generated project, decides, and the next period changes in response. NOTHING IN THIS RUN
GENERATES A TRAINING PROJECT OR ADVANCES A PERIOD. Later runs build that. This module builds
only the two things that must exist before any of it: the flag that turns the feature on, and
the refusal that keeps a research account off it wherever the flag is set.

WHY THIS IS ENFORCED ON THE SERVER, THE SAME WAY THEME AND THE TECHNICAL REVIEWER ARE

A previous session found an anonymous `getportfoliohealth` bypassing a flag that a signed-in
user with it off was held to (`gate_action` leaves a sessionless caller alone, because most
gated actions have nothing to check without a session). A hidden nav item is not a gate for the
same reason: hiding the "Train" tab stops a browser from showing the control, and says nothing
about a caller who posts the action directly. So `a_trainingstatus` below resolves the caller
itself, the same defence-in-depth `a_themeset` uses for the research refusal it is already
covered by upstream — refusing an ABSENT session on its own, before it ever asks what the flag
says, closes exactly the gap the previous session found.

RESEARCH IS REFUSED UNCONDITIONALLY, NOT BY THE FLAG DEFAULTING OFF. `default_for_account`
already defaults a research account's flags to disabled, so an admin who never touches the
`training` key gets the right answer by accident. That is not enough: an admin CAN set
`training: true` on a research participant's row (nothing today stops them, and archiving or
reassigning an account does not clear stored features), and the moment that happens the
default-off protection is gone. `training` is listed in `RESEARCH_FORBIDDEN_ACTIONS` for exactly
the reason `themeset` and `projectcreate` are: the refusal must not depend on nobody having
flipped the flag by mistake.
"""

from __future__ import annotations

from typing import Any, Callable

from sqlalchemy.orm import Session

from .facade import err
from .features import feature_enabled
from .research_identity import audit, resolve_caller

__all__ = ["TRAINING_ACTIONS"]


def a_trainingstatus(session: Session, payload: dict, secret: str, ttl: int) -> dict[str, Any]:
    """
    Whether this caller may use training mode right now.

    Read-only, and safe to call before the "Train" nav item is drawn: the frontend uses this to
    decide whether to show the tab at all, but showing the tab is a convenience, not the
    enforcement. Every action this run does not yet build will register under the same
    `GATED_ACTIONS["training"]` key and go through the identical two checks.
    """
    caller, problem = resolve_caller(session, payload, secret)
    if problem:
        return problem
    participant = caller.participant

    if participant.account_type == "research":
        # Redundant with `gate_action`'s RESEARCH_FORBIDDEN_ACTIONS refusal (features.py), which
        # runs before this handler is ever reached. Repeated here for the same reason
        # `a_themeset` repeats its own check: a handler that assumes an upstream gate is a
        # handler that breaks silently the day the gate is refactored.
        audit(session, "training_denied_research", participant_id=caller.participant_id,
              account_type=participant.account_type)
        session.commit()
        return err("not available for this account: training mode is an operational feature.")

    enabled = feature_enabled(session, participant, "training")
    return {
        "ok": True,
        "participant_id": caller.participant_id,
        "account_type": participant.account_type,
        "enabled": enabled,
    }


TRAINING_ACTIONS: dict[str, Callable[[Session, dict, str, int], dict]] = {
    "trainingstatus": a_trainingstatus,
}
