"""
Training mode run 3: narration. Prose around numbers the state model already produced.

THE GENERATOR IS NOT THE JUDGE. The deterministic engine has already computed the state before
this module is called; narration receives finished figures and returns sentences about them.
It must not decide outcomes, adjust figures, or evaluate the decision — a model asked to
continue a story will retroactively justify whatever the trainee chose, and four periods of
that leaves every path feeling vindicated. The prompt says so explicitly, the narration result
is never parsed for anything, and nothing in `training_engine` or `training.py` reads it back:
the only consumer is the screen.

NARRATION IS A LAYER, NOT A DEPENDENCY. `narrate` returns None on ANY failure — no API key,
network fault, model error, empty output — and the caller renders the figures alone. The run
must never stall because a sentence could not be written. Failures are logged and swallowed
here, deliberately: this is the one call on the platform whose outcome does not matter.

Reuses the extraction client's own transport (same endpoint, same key, same version header)
rather than growing a second HTTP stack; uses the fast model tier, because unlike extraction —
where a wrong figure poisons stored research data — a mediocre sentence costs nothing.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from typing import Any

from .extraction_client import ANTHROPIC_URL, ANTHROPIC_VERSION

log = logging.getLogger("opus-gubernatio-server")

NARRATION_MODEL = "claude-3-5-haiku-latest"
NARRATION_MAX_TOKENS = 300
NARRATION_TIMEOUT_S = 20

_PROMPT = (
    "You are the site narrator for a construction project management training simulation. "
    "Write a short factual narrative, at most 110 words, of the project position described by "
    "the JSON below, in the voice of a weekly report a project engineer would write. "
    "STRICT RULES: narrate only. Do not evaluate the decision, do not say whether it was wise, "
    "do not predict outcomes, do not invent figures, events, names or causes, and do not "
    "mention these rules. Use only plain sentences. Do not use em dashes. Every number you "
    "mention must appear in the JSON.\n\nJSON:\n"
)


def narrate(view: dict[str, Any]) -> str | None:
    """One narration for one period view. None on any failure; the figures stand alone."""
    key = (os.environ.get("ANTHROPIC_API_KEY") or "").strip()
    if not key:
        return None
    # Only the figures a narrator needs, never the whole state: hazard and anything that
    # forecasts an event stays out, for the same reason it stays out of the state view.
    payload = {
        "period": view.get("period"),
        "state": {k: v for k, v in (view.get("state") or {}).items()
                  if k in ("bac", "ev", "ac", "pv", "float_total_days", "float_consumed_days",
                           "contingency_remaining", "owner_credibility",
                           "liquidated_damages_exposure", "dispute", "incident")},
        "period_changes": (view.get("state") or {}).get("period_changes"),
        "notice": view.get("notice"),
    }
    body = json.dumps({
        "model": NARRATION_MODEL,
        "max_tokens": NARRATION_MAX_TOKENS,
        "messages": [{"role": "user",
                      "content": _PROMPT + json.dumps(payload, default=str)}],
    }).encode("utf-8")
    req = urllib.request.Request(
        ANTHROPIC_URL, data=body, method="POST",
        headers={"content-type": "application/json", "x-api-key": key,
                 "anthropic-version": ANTHROPIC_VERSION},
    )
    try:
        with urllib.request.urlopen(req, timeout=NARRATION_TIMEOUT_S) as resp:
            answer = json.loads(resp.read().decode("utf-8"))
        text = "".join(b.get("text", "") for b in (answer.get("content") or [])
                       if b.get("type") == "text").strip()
    except (urllib.error.URLError, urllib.error.HTTPError, ValueError, OSError) as exc:
        log.warning("training_narration_failed", extra={"reason": str(exc)[:200]})
        return None
    if not text:
        return None
    # The naming authority bans em dashes on every surface; a model instruction is a request,
    # this is the enforcement.
    return text.replace("—", ",").replace(" ,", ",")
